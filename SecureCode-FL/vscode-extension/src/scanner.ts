/**
 * Vulnerability Scanner - Analyzes code and detects vulnerabilities
 */

import * as vscode from 'vscode';
import { ServerClient, VulnerabilityResult } from './serverClient';
import { DiagnosticsManager } from './diagnostics';

export class VulnerabilityScanner {
    private serverClient: ServerClient;
    private diagnosticsManager: DiagnosticsManager;
    private cache: Map<string, { hash: string; results: VulnerabilityResult[] }> = new Map();

    constructor(serverClient: ServerClient, diagnosticsManager: DiagnosticsManager) {
        this.serverClient = serverClient;
        this.diagnosticsManager = diagnosticsManager;
    }

    async scanDocument(document: vscode.TextDocument): Promise<VulnerabilityResult[]> {
        const code = document.getText();
        const filename = document.fileName;
        const language = document.languageId;

        // Check cache
        const codeHash = this.hashCode(code);
        const cached = this.cache.get(filename);
        if (cached && cached.hash === codeHash) {
            return cached.results;
        }

        try {
            const response = await this.serverClient.scanCode(code, language, filename);
            
            if (response.success) {
                // Filter by minimum confidence
                const minConfidence = vscode.workspace.getConfiguration('securecode-fl')
                    .get('minimumConfidence', 0.7);
                
                const vulnerabilities = response.vulnerabilities.filter(
                    v => v.confidence >= minConfidence
                );

                // Update diagnostics
                this.diagnosticsManager.updateDiagnostics(document, vulnerabilities);

                // Update cache
                this.cache.set(filename, { hash: codeHash, results: vulnerabilities });

                return vulnerabilities;
            }
            
            return [];
        } catch (error) {
            // If server is unavailable, use local fallback detection
            console.warn('Server unavailable, using local pattern matching:', error);
            const localResults = this.localPatternScan(document);
            this.diagnosticsManager.updateDiagnostics(document, localResults);
            return localResults;
        }
    }

    /**
     * Local pattern-based scanning as fallback when server is unavailable
     */
    private localPatternScan(document: vscode.TextDocument): VulnerabilityResult[] {
        const vulnerabilities: VulnerabilityResult[] = [];
        const text = document.getText();
        const lines = text.split('\n');

        // Define vulnerability patterns
        const patterns = [
            {
                regex: /password\s*=\s*["'][^"']+["']/gi,
                type: 'Broken Authentication',
                severity: 'high' as const,
                message: 'Hardcoded password detected',
                suggestion: 'Use environment variables or a secure secrets manager',
                cwe_id: 'CWE-798'
            },
            {
                regex: /api[_-]?key\s*=\s*["'][^"']+["']/gi,
                type: 'Security Misconfiguration',
                severity: 'high' as const,
                message: 'Hardcoded API key detected',
                suggestion: 'Store API keys in environment variables',
                cwe_id: 'CWE-798'
            },
            {
                regex: /eval\s*\(/gi,
                type: 'Unsafe Consumption of APIs',
                severity: 'high' as const,
                message: 'Use of eval() is dangerous',
                suggestion: 'Avoid eval() - use safer alternatives like JSON.parse()',
                cwe_id: 'CWE-95'
            },
            {
                regex: /exec\s*\(/gi,
                type: 'Unsafe Consumption of APIs',
                severity: 'high' as const,
                message: 'Use of exec() can lead to code injection',
                suggestion: 'Validate and sanitize all inputs before execution',
                cwe_id: 'CWE-78'
            },
            {
                regex: /SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\+/gi,
                type: 'Broken Object Level Authorization',
                severity: 'high' as const,
                message: 'Potential SQL injection vulnerability',
                suggestion: 'Use parameterized queries or prepared statements',
                cwe_id: 'CWE-89'
            },
            {
                regex: /\.innerHTML\s*=/gi,
                type: 'Unsafe Consumption of APIs',
                severity: 'medium' as const,
                message: 'innerHTML can lead to XSS vulnerabilities',
                suggestion: 'Use textContent or sanitize HTML input',
                cwe_id: 'CWE-79'
            },
            {
                regex: /http:\/\//gi,
                type: 'Security Misconfiguration',
                severity: 'low' as const,
                message: 'Insecure HTTP protocol detected',
                suggestion: 'Use HTTPS for secure communication',
                cwe_id: 'CWE-319'
            },
            {
                regex: /verify\s*=\s*False/gi,
                type: 'Broken Authentication',
                severity: 'high' as const,
                message: 'SSL verification disabled',
                suggestion: 'Enable SSL certificate verification',
                cwe_id: 'CWE-295'
            },
            {
                regex: /sleep\s*\(\s*\d+\s*\)/gi,
                type: 'Unrestricted Resource Consumption',
                severity: 'low' as const,
                message: 'Fixed sleep can cause DoS vulnerabilities',
                suggestion: 'Use configurable timeouts',
                cwe_id: 'CWE-400'
            },
            {
                regex: /DEBUG\s*=\s*True/gi,
                type: 'Security Misconfiguration',
                severity: 'medium' as const,
                message: 'Debug mode enabled in code',
                suggestion: 'Disable debug mode in production',
                cwe_id: 'CWE-489'
            }
        ];

        // Scan each line
        lines.forEach((line, lineIndex) => {
            patterns.forEach(pattern => {
                const matches = line.matchAll(pattern.regex);
                for (const match of matches) {
                    const startColumn = match.index || 0;
                    const endColumn = startColumn + match[0].length;

                    vulnerabilities.push({
                        line: lineIndex + 1,
                        column: startColumn,
                        endLine: lineIndex + 1,
                        endColumn: endColumn,
                        vulnerability_type: pattern.type,
                        confidence: 0.85, // High confidence for pattern matches
                        severity: pattern.severity,
                        message: pattern.message,
                        suggestion: pattern.suggestion,
                        cwe_id: pattern.cwe_id,
                        owasp_category: pattern.type
                    });
                }
            });
        });

        return vulnerabilities;
    }

    private hashCode(str: string): string {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return hash.toString();
    }

    clearCache(): void {
        this.cache.clear();
    }
}
