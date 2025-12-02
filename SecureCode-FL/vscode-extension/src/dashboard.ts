/**
 * Dashboard Panel - WebView panel showing vulnerability overview
 */

import * as vscode from 'vscode';

export class DashboardPanel {
    public static currentPanel: DashboardPanel | undefined;
    private static readonly viewType = 'securecodeDashboard';

    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (DashboardPanel.currentPanel) {
            DashboardPanel.currentPanel._panel.reveal(column);
            return;
        }

        // Create a new panel
        const panel = vscode.window.createWebviewPanel(
            DashboardPanel.viewType,
            'SecureCode-FL Dashboard',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')]
            }
        );

        DashboardPanel.currentPanel = new DashboardPanel(panel, extensionUri);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;

        // Set initial HTML content
        this._update();

        // Listen for when the panel is disposed
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Update content when view changes
        this._panel.onDidChangeViewState(
            () => {
                if (this._panel.visible) {
                    this._update();
                }
            },
            null,
            this._disposables
        );

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'scanWorkspace':
                        vscode.commands.executeCommand('securecode-fl.scanWorkspace');
                        break;
                    case 'openFile':
                        vscode.workspace.openTextDocument(message.file).then(doc => {
                            vscode.window.showTextDocument(doc);
                        });
                        break;
                }
            },
            null,
            this._disposables
        );
    }

    public dispose() {
        DashboardPanel.currentPanel = undefined;

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }

    private _update() {
        this._panel.webview.html = this._getHtmlContent();
    }

    private _getHtmlContent(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecureCode-FL Dashboard</title>
    <style>
        :root {
            --bg-primary: #1e1e1e;
            --bg-secondary: #252526;
            --bg-tertiary: #2d2d30;
            --text-primary: #cccccc;
            --text-secondary: #969696;
            --accent-blue: #007acc;
            --accent-green: #4ec9b0;
            --severity-high: #f14c4c;
            --severity-medium: #cca700;
            --severity-low: #3794ff;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
            margin: 0;
        }

        .header {
            display: flex;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--bg-tertiary);
        }

        .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }

        .header .logo {
            font-size: 32px;
            margin-right: 15px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--accent-blue);
        }

        .stat-card.high {
            border-left-color: var(--severity-high);
        }

        .stat-card.medium {
            border-left-color: var(--severity-medium);
        }

        .stat-card.low {
            border-left-color: var(--severity-low);
        }

        .stat-card.secure {
            border-left-color: var(--accent-green);
        }

        .stat-card h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
        }

        .stat-card .value {
            font-size: 32px;
            font-weight: 600;
        }

        .section {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .section h2 {
            margin: 0 0 15px 0;
            font-size: 18px;
            font-weight: 600;
        }

        .vuln-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .vuln-item {
            display: flex;
            align-items: center;
            padding: 12px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            margin-bottom: 8px;
        }

        .vuln-item .icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            font-size: 16px;
        }

        .vuln-item.high .icon {
            background: rgba(241, 76, 76, 0.2);
            color: var(--severity-high);
        }

        .vuln-item.medium .icon {
            background: rgba(204, 167, 0, 0.2);
            color: var(--severity-medium);
        }

        .vuln-item.low .icon {
            background: rgba(55, 148, 255, 0.2);
            color: var(--severity-low);
        }

        .vuln-item .details {
            flex: 1;
        }

        .vuln-item .type {
            font-weight: 600;
            margin-bottom: 4px;
        }

        .vuln-item .file {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .btn {
            background: var(--accent-blue);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }

        .btn:hover {
            background: #005a9e;
        }

        .model-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .model-info .item {
            padding: 10px;
            background: var(--bg-tertiary);
            border-radius: 4px;
        }

        .model-info .label {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .model-info .value {
            font-size: 14px;
            font-weight: 600;
            margin-top: 4px;
        }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }

        .empty-state .icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="header">
        <span class="logo">🛡️</span>
        <h1>SecureCode-FL Dashboard</h1>
    </div>

    <div class="stats-grid">
        <div class="stat-card secure">
            <h3>Files Scanned</h3>
            <div class="value" id="filesScanned">0</div>
        </div>
        <div class="stat-card high">
            <h3>High Severity</h3>
            <div class="value" id="highCount">0</div>
        </div>
        <div class="stat-card medium">
            <h3>Medium Severity</h3>
            <div class="value" id="mediumCount">0</div>
        </div>
        <div class="stat-card low">
            <h3>Low Severity</h3>
            <div class="value" id="lowCount">0</div>
        </div>
    </div>

    <div class="section">
        <h2>🔍 Actions</h2>
        <button class="btn" onclick="scanWorkspace()">Scan Workspace</button>
        <button class="btn" onclick="refreshDashboard()">Refresh</button>
    </div>

    <div class="section">
        <h2>🤖 Model Information</h2>
        <div class="model-info">
            <div class="item">
                <div class="label">Model Type</div>
                <div class="value">Federated Learning MLP</div>
            </div>
            <div class="item">
                <div class="label">Accuracy</div>
                <div class="value">94.7%</div>
            </div>
            <div class="item">
                <div class="label">Training Method</div>
                <div class="value">FedAvg (3 clients)</div>
            </div>
            <div class="item">
                <div class="label">Vulnerability Types</div>
                <div class="value">OWASP API Top 10</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📋 Recent Vulnerabilities</h2>
        <div class="empty-state" id="emptyState">
            <div class="icon">✅</div>
            <p>No vulnerabilities detected yet.<br>Click "Scan Workspace" to begin.</p>
        </div>
        <ul class="vuln-list" id="vulnList" style="display: none;"></ul>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function scanWorkspace() {
            vscode.postMessage({ command: 'scanWorkspace' });
        }

        function refreshDashboard() {
            location.reload();
        }

        function openFile(file) {
            vscode.postMessage({ command: 'openFile', file: file });
        }
    </script>
</body>
</html>`;
    }
}
