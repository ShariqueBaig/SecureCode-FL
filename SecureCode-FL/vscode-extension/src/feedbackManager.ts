/**
 * Feedback Manager - Handles user feedback on vulnerability detections
 * 
 * Allows users to:
 * - Mark detections as false positives
 * - Report missed vulnerabilities
 * - Confirm or dispute detections
 * 
 * Feedback is stored locally and used for federated model improvement.
 */

import * as vscode from 'vscode';
import { ServerClient } from './serverClient';

export interface FeedbackData {
    code_snippet: string;
    user_label: 'vulnerable' | 'secure';
    start_line: number;
    end_line: number;
    start_column: number;
    end_column: number;
    original_detection?: string;
    severity?: 'high' | 'medium' | 'low';
    vulnerability_type?: string;
    notes?: string;
    file_path: string;
    language: string;
}

export class FeedbackManager {
    private serverClient: ServerClient;

    constructor(serverClient: ServerClient) {
        this.serverClient = serverClient;
    }

    /**
     * Mark the selected code as a false positive (incorrectly flagged)
     */
    async markAsFalsePositive(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        const selection = editor.selection;
        if (selection.isEmpty) {
            vscode.window.showWarningMessage('Please select the code to mark as a false positive');
            return;
        }

        const selectedText = editor.document.getText(selection);
        
        // Get notes from user
        const notes = await vscode.window.showInputBox({
            prompt: 'Why is this a false positive? (optional)',
            placeHolder: 'e.g., This uses environment variables, not hardcoded secrets'
        });

        // Get the original detection from diagnostics at this location
        const diagnostics = vscode.languages.getDiagnostics(editor.document.uri);
        const relevantDiagnostic = diagnostics.find(d => 
            d.source === 'SecureCode-FL' && 
            selection.contains(d.range)
        );

        const feedbackData: FeedbackData = {
            code_snippet: selectedText,
            user_label: 'secure',
            start_line: selection.start.line + 1,
            end_line: selection.end.line + 1,
            start_column: selection.start.character,
            end_column: selection.end.character,
            original_detection: relevantDiagnostic?.code?.toString() || relevantDiagnostic?.message?.split(']')[0]?.replace('[', ''),
            notes: notes || undefined,
            file_path: editor.document.fileName,
            language: editor.document.languageId
        };

        await this.submitFeedback(feedbackData, 'false positive');
    }

    /**
     * Mark the selected code as vulnerable (missed by detection)
     */
    async markAsVulnerable(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        const selection = editor.selection;
        if (selection.isEmpty) {
            vscode.window.showWarningMessage('Please select the vulnerable code');
            return;
        }

        const selectedText = editor.document.getText(selection);

        // Get vulnerability type from user
        const vulnerabilityTypes = await this.serverClient.getVulnerabilityTypes();
        const selectedType = await vscode.window.showQuickPick(
            ['Other - Describe Below', ...vulnerabilityTypes],
            {
                placeHolder: 'Select the type of vulnerability',
                title: 'Vulnerability Type'
            }
        );

        if (!selectedType) {
            return; // User cancelled
        }

        // Get severity
        const severity = await vscode.window.showQuickPick(
            ['high', 'medium', 'low'],
            {
                placeHolder: 'Select severity level',
                title: 'Vulnerability Severity'
            }
        ) as 'high' | 'medium' | 'low' | undefined;

        if (!severity) {
            return; // User cancelled
        }

        // Get notes/description
        const notes = await vscode.window.showInputBox({
            prompt: 'Describe the vulnerability',
            placeHolder: 'e.g., This SQL query is vulnerable to injection attacks'
        });

        const feedbackData: FeedbackData = {
            code_snippet: selectedText,
            user_label: 'vulnerable',
            start_line: selection.start.line + 1,
            end_line: selection.end.line + 1,
            start_column: selection.start.character,
            end_column: selection.end.character,
            severity: severity,
            vulnerability_type: selectedType === 'Other - Describe Below' ? notes : selectedType,
            notes: notes || undefined,
            file_path: editor.document.fileName,
            language: editor.document.languageId
        };

        await this.submitFeedback(feedbackData, 'vulnerability report');
    }

    /**
     * Confirm that a detection is correct
     */
    async confirmVulnerability(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        // Get diagnostics at cursor position
        const position = editor.selection.active;
        const diagnostics = vscode.languages.getDiagnostics(editor.document.uri);
        const relevantDiagnostics = diagnostics.filter(d => 
            d.source === 'SecureCode-FL' && 
            d.range.contains(position)
        );

        if (relevantDiagnostics.length === 0) {
            vscode.window.showWarningMessage('No SecureCode-FL detection at cursor position');
            return;
        }

        // If multiple, let user choose
        let diagnostic = relevantDiagnostics[0];
        if (relevantDiagnostics.length > 1) {
            const items = relevantDiagnostics.map(d => ({
                label: d.message.split('\n')[0],
                diagnostic: d
            }));
            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Which detection do you want to confirm?'
            });
            if (!selected) {
                return;
            }
            diagnostic = selected.diagnostic;
        }

        const codeSnippet = editor.document.getText(diagnostic.range);

        const feedbackData: FeedbackData = {
            code_snippet: codeSnippet,
            user_label: 'vulnerable',
            start_line: diagnostic.range.start.line + 1,
            end_line: diagnostic.range.end.line + 1,
            start_column: diagnostic.range.start.character,
            end_column: diagnostic.range.end.character,
            original_detection: diagnostic.code?.toString(),
            file_path: editor.document.fileName,
            language: editor.document.languageId
        };

        await this.submitFeedback(feedbackData, 'confirmation');
    }

    /**
     * Show feedback statistics
     */
    async showFeedbackStats(): Promise<void> {
        try {
            const stats = await this.serverClient.getFeedbackStats();
            
            const message = [
                `📊 Feedback Statistics`,
                ``,
                `Total Entries: ${stats.total}`,
                `Untrained: ${stats.untrained}`,
                ``,
                `By Type:`,
                ...Object.entries(stats.by_type || {}).map(([type, count]) => `  - ${type}: ${count}`),
                ``,
                `By Label:`,
                ...Object.entries(stats.by_label || {}).map(([label, count]) => `  - ${label}: ${count}`)
            ].join('\n');

            vscode.window.showInformationMessage(message, { modal: true });
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to get feedback stats: ${error}`);
        }
    }

    /**
     * Submit feedback to the server
     */
    private async submitFeedback(data: FeedbackData, feedbackType: string): Promise<void> {
        try {
            const result = await this.serverClient.submitFeedback(data);
            
            if (result.success) {
                vscode.window.showInformationMessage(
                    `✅ Thank you! Your ${feedbackType} has been recorded and will help improve the model.`
                );
            } else {
                if (result.existing_id) {
                    vscode.window.showWarningMessage(
                        `Feedback already exists for this code snippet (ID: ${result.existing_id})`
                    );
                } else {
                    vscode.window.showWarningMessage(`Failed to submit feedback: ${result.message}`);
                }
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to submit feedback: ${error}`);
        }
    }
}

/**
 * Code action provider for feedback-related quick fixes
 */
export class FeedbackCodeActionProvider implements vscode.CodeActionProvider {
    private feedbackManager: FeedbackManager;

    constructor(feedbackManager: FeedbackManager) {
        this.feedbackManager = feedbackManager;
    }

    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range,
        context: vscode.CodeActionContext
    ): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];

        // Check if there are SecureCode-FL diagnostics
        const secureCodeDiagnostics = context.diagnostics.filter(d => d.source === 'SecureCode-FL');

        if (secureCodeDiagnostics.length > 0) {
            // Add "Mark as False Positive" action
            const falsePositiveAction = new vscode.CodeAction(
                '✗ Mark as False Positive',
                vscode.CodeActionKind.QuickFix
            );
            falsePositiveAction.command = {
                command: 'securecode-fl.markFalsePositive',
                title: 'Mark as False Positive'
            };
            actions.push(falsePositiveAction);

            // Add "Confirm Vulnerability" action
            const confirmAction = new vscode.CodeAction(
                '✓ Confirm Vulnerability',
                vscode.CodeActionKind.QuickFix
            );
            confirmAction.command = {
                command: 'securecode-fl.confirmVulnerability',
                title: 'Confirm Vulnerability'
            };
            actions.push(confirmAction);
        }

        return actions;
    }
}
