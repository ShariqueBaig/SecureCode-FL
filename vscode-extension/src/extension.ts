/**
 * SecureCode-FL VS Code Extension
 * Real-time code vulnerability detection powered by Federated Learning
 * With User Feedback System for Model Improvement
 */

import * as vscode from 'vscode';
import { VulnerabilityScanner } from './scanner';
import { DiagnosticsManager } from './diagnostics';
import { DashboardPanel } from './dashboard';
import { ServerClient } from './serverClient';
import { FeedbackManager, FeedbackCodeActionProvider } from './feedbackManager';

let scanner: VulnerabilityScanner;
let diagnosticsManager: DiagnosticsManager;
let serverClient: ServerClient;
let feedbackManager: FeedbackManager;
let statusBarItem: vscode.StatusBarItem;
let realTimeScanningEnabled: boolean = true;
let scanTimeout: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext) {
    console.log('SecureCode-FL extension is now active!');

    // Initialize components
    serverClient = new ServerClient();
    diagnosticsManager = new DiagnosticsManager();
    scanner = new VulnerabilityScanner(serverClient, diagnosticsManager);
    feedbackManager = new FeedbackManager(serverClient);

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = "$(shield) SecureCode-FL";
    statusBarItem.tooltip = "Click to scan current file";
    statusBarItem.command = 'securecode-fl.scanFile';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('securecode-fl.scanFile', () => scanCurrentFile()),
        vscode.commands.registerCommand('securecode-fl.scanWorkspace', () => scanWorkspace()),
        vscode.commands.registerCommand('securecode-fl.toggleRealTime', () => toggleRealTimeScanning()),
        vscode.commands.registerCommand('securecode-fl.showDashboard', () => DashboardPanel.createOrShow(context.extensionUri)),
        // Feedback commands
        vscode.commands.registerCommand('securecode-fl.markFalsePositive', () => feedbackManager.markAsFalsePositive()),
        vscode.commands.registerCommand('securecode-fl.markVulnerable', () => feedbackManager.markAsVulnerable()),
        vscode.commands.registerCommand('securecode-fl.confirmVulnerability', () => feedbackManager.confirmVulnerability()),
        vscode.commands.registerCommand('securecode-fl.showFeedbackStats', () => feedbackManager.showFeedbackStats())
    );

    // Register diagnostics collection
    context.subscriptions.push(diagnosticsManager.diagnosticCollection);

    // Register code action provider for quick fixes
    const codeActionProvider = new FeedbackCodeActionProvider(feedbackManager);
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            ['python'],
            codeActionProvider,
            { providedCodeActionKinds: [vscode.CodeActionKind.QuickFix] }
        )
    );

    // Real-time scanning on document change
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument((event) => {
            if (realTimeScanningEnabled && isSupportedLanguage(event.document)) {
                // Debounce scanning
                if (scanTimeout) {
                    clearTimeout(scanTimeout);
                }
                const delay = vscode.workspace.getConfiguration('securecode-fl').get('scanDelay', 1000);
                scanTimeout = setTimeout(() => {
                    scanDocument(event.document);
                }, delay);
            }
        })
    );

    // Scan on document open
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument((document) => {
            if (realTimeScanningEnabled && isSupportedLanguage(document)) {
                scanDocument(document);
            }
        })
    );

    // Scan currently open document
    if (vscode.window.activeTextEditor && isSupportedLanguage(vscode.window.activeTextEditor.document)) {
        scanDocument(vscode.window.activeTextEditor.document);
    }

    // Check server connection
    checkServerConnection();
}

async function scanCurrentFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No file is currently open');
        return;
    }

    if (!isSupportedLanguage(editor.document)) {
        vscode.window.showWarningMessage('This file type is not supported for vulnerability scanning');
        return;
    }

    await scanDocument(editor.document, true);
}

async function scanDocument(document: vscode.TextDocument, showNotification: boolean = false) {
    try {
        updateStatusBar('$(sync~spin) Scanning...', 'Scanning for vulnerabilities...');

        const vulnerabilities = await scanner.scanDocument(document);

        if (vulnerabilities.length === 0) {
            updateStatusBar('$(shield) Secure', 'No vulnerabilities detected');
            if (showNotification) {
                vscode.window.showInformationMessage('✅ No vulnerabilities detected!');
            }
        } else {
            updateStatusBar(`$(warning) ${vulnerabilities.length} issues`, `${vulnerabilities.length} vulnerabilities detected`);
            if (showNotification) {
                vscode.window.showWarningMessage(
                    `⚠️ Found ${vulnerabilities.length} potential vulnerabilities`,
                    'Show Details'
                ).then(selection => {
                    if (selection === 'Show Details') {
                        vscode.commands.executeCommand('workbench.action.problems.focus');
                    }
                });
            }
        }
    } catch (error) {
        updateStatusBar('$(error) Error', 'Failed to scan file');
        if (showNotification) {
            vscode.window.showErrorMessage(`Scan failed: ${error}`);
        }
    }
}

async function scanWorkspace() {
    const files = await vscode.workspace.findFiles(
        '**/*.{py,js,ts,java,cs,php}',
        '**/node_modules/**'
    );

    if (files.length === 0) {
        vscode.window.showInformationMessage('No supported files found in workspace');
        return;
    }

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "SecureCode-FL: Scanning workspace",
        cancellable: true
    }, async (progress, token) => {
        let totalVulnerabilities = 0;

        for (let i = 0; i < files.length; i++) {
            if (token.isCancellationRequested) {
                break;
            }

            progress.report({
                message: `Scanning ${i + 1}/${files.length}: ${files[i].fsPath.split(/[\\/]/).pop()}`,
                increment: (100 / files.length)
            });

            try {
                const document = await vscode.workspace.openTextDocument(files[i]);
                const vulnerabilities = await scanner.scanDocument(document);
                totalVulnerabilities += vulnerabilities.length;
            } catch (error) {
                console.error(`Error scanning ${files[i].fsPath}:`, error);
            }
        }

        if (totalVulnerabilities === 0) {
            vscode.window.showInformationMessage('✅ Workspace scan complete: No vulnerabilities found!');
        } else {
            vscode.window.showWarningMessage(
                `⚠️ Workspace scan complete: Found ${totalVulnerabilities} potential vulnerabilities`,
                'Show Problems'
            ).then(selection => {
                if (selection === 'Show Problems') {
                    vscode.commands.executeCommand('workbench.action.problems.focus');
                }
            });
        }
    });
}

function toggleRealTimeScanning() {
    realTimeScanningEnabled = !realTimeScanningEnabled;

    if (realTimeScanningEnabled) {
        vscode.window.showInformationMessage('Real-time scanning enabled');
        updateStatusBar('$(shield) SecureCode-FL', 'Real-time scanning enabled');
    } else {
        vscode.window.showInformationMessage('Real-time scanning disabled');
        updateStatusBar('$(shield-off) SecureCode-FL', 'Real-time scanning disabled');
        diagnosticsManager.clearAll();
    }
}

function updateStatusBar(text: string, tooltip: string) {
    statusBarItem.text = text;
    statusBarItem.tooltip = tooltip;
}

function isSupportedLanguage(document: vscode.TextDocument): boolean {
    const supportedLanguages = ['python'];
    return supportedLanguages.includes(document.languageId);
}

async function checkServerConnection() {
    try {
        const isConnected = await serverClient.healthCheck();
        if (!isConnected) {
            vscode.window.showWarningMessage(
                'SecureCode-FL server is not running. Start the server for vulnerability detection.',
                'Start Server'
            ).then(selection => {
                if (selection === 'Start Server') {
                    vscode.window.showInformationMessage(
                        'Run: python -m inference_server.server in the SecureCode-FL directory'
                    );
                }
            });
        }
    } catch (error) {
        console.error('Server health check failed:', error);
    }
}

export function deactivate() {
    if (scanTimeout) {
        clearTimeout(scanTimeout);
    }
    diagnosticsManager.clearAll();
}
