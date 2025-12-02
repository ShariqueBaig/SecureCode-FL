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

export interface FeedbackResponse {
    success: boolean;
    feedback_id?: number;
    feedback_type?: string;
    message?: string;
    existing_id?: number;
}

export interface FeedbackStats {
    total: number;
    untrained: number;
    by_type: Record<string, number>;
    by_label: Record<string, number>;
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

    /**
     * Submit user feedback on a vulnerability detection
     */
    async submitFeedback(data: FeedbackData): Promise<FeedbackResponse> {
        try {
            const response = await this.client.post('/feedback', data);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error) && error.response?.status === 409) {
                // Feedback already exists
                return {
                    success: false,
                    message: 'Feedback already exists for this code',
                    existing_id: error.response.data.existing_id
                };
            }
            throw new Error('Failed to submit feedback');
        }
    }

    /**
     * Get feedback statistics
     */
    async getFeedbackStats(): Promise<FeedbackStats> {
        try {
            const response = await this.client.get('/feedback/stats');
            return response.data.stats;
        } catch (error) {
            throw new Error('Failed to get feedback stats');
        }
    }

    /**
     * Get all feedback entries
     */
    async listFeedback(): Promise<any[]> {
        try {
            const response = await this.client.get('/feedback/list');
            return response.data.feedback;
        } catch (error) {
            throw new Error('Failed to list feedback');
        }
    }

    /**
     * Delete a feedback entry
     */
    async deleteFeedback(feedbackId: number): Promise<boolean> {
        try {
            const response = await this.client.delete(`/feedback/${feedbackId}`);
            return response.data.success;
        } catch (error) {
            return false;
        }
    }
}
