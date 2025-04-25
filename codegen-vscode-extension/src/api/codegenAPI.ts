import axios, { type AxiosInstance } from "axios";
import * as vscode from "vscode";

export interface CodegenResponse {
	text: string;
	code?: string;
	language?: string;
}

export class CodegenAPI {
	private client: AxiosInstance;
	private apiKey = "";
	private endpoint = "";

	constructor() {
		this.loadConfiguration();

		this.client = axios.create({
			baseURL: this.endpoint,
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${this.apiKey}`,
			},
		});

		// Listen for configuration changes
		vscode.workspace.onDidChangeConfiguration((e) => {
			if (
				e.affectsConfiguration("codegen.apiKey") ||
				e.affectsConfiguration("codegen.endpoint")
			) {
				this.loadConfiguration();
				this.updateClient();
			}
		});
	}

	private loadConfiguration() {
		const config = vscode.workspace.getConfiguration("codegen");
		this.apiKey = config.get<string>("apiKey") || "";
		this.endpoint = config.get<string>("endpoint") || "https://api.codegen.sh";
	}

	private updateClient() {
		this.client = axios.create({
			baseURL: this.endpoint,
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${this.apiKey}`,
			},
		});
	}

	public async validateApiKey(): Promise<boolean> {
		if (!this.apiKey) {
			return false;
		}

		try {
			// Make a simple request to validate the API key
			await this.client.get("/api/validate");
			return true;
		} catch (error) {
			console.error("API key validation failed:", error);
			return false;
		}
	}

	public async askQuestion(
		question: string,
		context?: string,
	): Promise<CodegenResponse> {
		try {
			const response = await this.client.post("/api/ask", {
				question,
				context,
			});

			return response.data;
		} catch (error) {
			console.error("Error asking question:", error);
			throw new Error("Failed to get response from Codegen API");
		}
	}

	public async generateCode(
		prompt: string,
		language?: string,
	): Promise<CodegenResponse> {
		try {
			const response = await this.client.post("/api/generate", {
				prompt,
				language,
			});

			return response.data;
		} catch (error) {
			console.error("Error generating code:", error);
			throw new Error("Failed to generate code from Codegen API");
		}
	}

	public async explainCode(
		code: string,
		language?: string,
	): Promise<CodegenResponse> {
		try {
			const response = await this.client.post("/api/explain", {
				code,
				language,
			});

			return response.data;
		} catch (error) {
			console.error("Error explaining code:", error);
			throw new Error("Failed to explain code from Codegen API");
		}
	}

	public async improveCode(
		code: string,
		language?: string,
	): Promise<CodegenResponse> {
		try {
			const response = await this.client.post("/api/improve", {
				code,
				language,
			});

			return response.data;
		} catch (error) {
			console.error("Error improving code:", error);
			throw new Error("Failed to improve code from Codegen API");
		}
	}

	public async fixCode(
		code: string,
		error?: string,
		language?: string,
	): Promise<CodegenResponse> {
		try {
			const response = await this.client.post("/api/fix", {
				code,
				error,
				language,
			});

			return response.data;
		} catch (error) {
			console.error("Error fixing code:", error);
			throw new Error("Failed to fix code from Codegen API");
		}
	}
}
