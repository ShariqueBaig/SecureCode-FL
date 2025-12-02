/**
 * Server Client - Communicates with the Python inference server
 */

import axios, { AxiosInstance } from 'axios';
import * as vscode from 'vscode';

export interface VulnerabilityResult {
    line: number;
    column: number;
    endLine: number;
    endColumn: number;
    vulnerability_type: string;
    confidence: number;
    severity: 'high' | 'medium' | 'low';
    message: string;
    suggestion: string;
    cwe_id?: string;
    owasp_category?: string;
}

export interface ScanResponse {
    success: boolean;
    vulnerabilities: VulnerabilityResult[];
    scan_time_ms: number;
    model_version: string;
}

export class ServerClient {
    private client: AxiosInstance;
    private isFirstRequest: boolean = true;

    constructor() {
        const serverUrl = vscode.workspace.getConfiguration('securecode-fl').get('serverUrl', 'http://localhost:5000');
        
        this.client = axios.create({
            baseURL: serverUrl,
            timeout: 60000, // Increased to 60 seconds for ML model inference
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async healthCheck(): Promise<boolean> {
        try {
            const response = await this.client.get('/health', { timeout: 10000 });
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }

    async scanCode(code: string, language: string, filename: string): Promise<ScanResponse> {
        try {
            // First request may take longer due to TensorFlow initialization
            const timeout = this.isFirstRequest ? 90000 : 60000;
            this.isFirstRequest = false;
            
            const response = await this.client.post('/scan', {
                code: code,
                language: language,
                filename: filename
            }, { timeout });
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error)) {
                if (error.code === 'ECONNREFUSED') {
                    throw new Error('Cannot connect to SecureCode-FL server. Please ensure the server is running.');
                }
                if (error.code === 'ETIMEDOUT' || error.message.includes('timeout')) {
                    throw new Error('Server timeout - ML model may still be loading. Please try again.');
                }
                throw new Error(`Server error: ${error.message}`);
            }
            throw error;
        }
    }

    async getModelInfo(): Promise<any> {
        try {
            const response = await this.client.get('/model/info');
            return response.data;
        } catch (error) {
            throw new Error('Failed to get model information');
        }
    }

    async getVulnerabilityTypes(): Promise<string[]> {
        try {
            const response = await this.client.get('/vulnerability-types');
            return response.data.types;
        } catch (error) {
            // Return default OWASP API Top 10 if server unavailable
            return [
                'Broken Object Level Authorization',
                'Broken Authentication',
                'Broken Object Property Level Authorization',
                'Unrestricted Resource Consumption',
                'Broken Function Level Authorization',
                'Unrestricted Access to Sensitive Business Flows',
                'Server Side Request Forgery',
                'Security Misconfiguration',
                'Improper Inventory Management',
                'Unsafe Consumption of APIs'
            ];
        }
    }
}
