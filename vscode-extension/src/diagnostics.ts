/**
 * Diagnostics Manager - Handles VS Code diagnostics (problems panel)
 */

import * as vscode from 'vscode';
import { VulnerabilityResult } from './serverClient';

export class DiagnosticsManager {
    public diagnosticCollection: vscode.DiagnosticCollection;

    constructor() {
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('securecode-fl');
    }

    updateDiagnostics(document: vscode.TextDocument, vulnerabilities: VulnerabilityResult[]): void {
        const diagnostics: vscode.Diagnostic[] = vulnerabilities.map(vuln => {
            const range = new vscode.Range(
                new vscode.Position(vuln.line - 1, vuln.column),
                new vscode.Position(vuln.endLine - 1, vuln.endColumn)
            );

            const severity = this.mapSeverity(vuln.severity);
            
            const diagnostic = new vscode.Diagnostic(
                range,
                `[${vuln.vulnerability_type}] ${vuln.message}\n💡 ${vuln.suggestion}`,
                severity
            );

            diagnostic.source = 'SecureCode-FL';
            diagnostic.code = vuln.cwe_id || vuln.owasp_category;
            
            // Add related information
            if (vuln.owasp_category) {
                diagnostic.relatedInformation = [
                    new vscode.DiagnosticRelatedInformation(
                        new vscode.Location(document.uri, range),
                        `OWASP: ${vuln.owasp_category} | Confidence: ${(vuln.confidence * 100).toFixed(1)}%`
                    )
                ];
            }

            return diagnostic;
        });

        this.diagnosticCollection.set(document.uri, diagnostics);
    }

    private mapSeverity(severity: 'high' | 'medium' | 'low'): vscode.DiagnosticSeverity {
        switch (severity) {
            case 'high':
                return vscode.DiagnosticSeverity.Error;
            case 'medium':
                return vscode.DiagnosticSeverity.Warning;
            case 'low':
                return vscode.DiagnosticSeverity.Information;
            default:
                return vscode.DiagnosticSeverity.Warning;
        }
    }

    clearAll(): void {
        this.diagnosticCollection.clear();
    }

    clearDocument(uri: vscode.Uri): void {
        this.diagnosticCollection.delete(uri);
    }
}
