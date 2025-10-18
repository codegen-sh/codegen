import * as vscode from "vscode";
import type { CodegenAPI } from "../api/codegenAPI";

interface ChatMessage {
	role: "user" | "assistant";
	content: string;
	code?: string;
	timestamp: number;
}

export class ChatViewProvider implements vscode.WebviewViewProvider {
	public static readonly viewType = "codegen.chatView";
	private _view?: vscode.WebviewView;
	private _messages: ChatMessage[] = [];

	constructor(
		private readonly _extensionUri: vscode.Uri,
		private readonly _api: CodegenAPI,
	) {}

	public resolveWebviewView(
		webviewView: vscode.WebviewView,
		context: vscode.WebviewViewResolveContext,
		_token: vscode.CancellationToken,
	) {
		this._view = webviewView;

		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [this._extensionUri],
		};

		webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

		// Handle messages from the webview
		webviewView.webview.onDidReceiveMessage(async (message) => {
			switch (message.command) {
				case "sendMessage":
					await this._handleUserMessage(message.text);
					break;
				case "clearChat":
					this._messages = [];
					this._updateWebview();
					break;
				case "insertCode":
					this._insertCodeToEditor(message.code);
					break;
			}
		});

		// Update the webview with existing messages
		this._updateWebview();
	}

	public addMessage(
		role: "user" | "assistant",
		content: string,
		code?: string,
	) {
		this._messages.push({
			role,
			content,
			code,
			timestamp: Date.now(),
		});

		this._updateWebview();
	}

	private async _handleUserMessage(text: string) {
		// Add user message to chat
		this.addMessage("user", text);

		try {
			// Show loading indicator
			this._view?.webview.postMessage({ command: "showLoading", value: true });

			// Get response from API
			const response = await this._api.askQuestion(text);

			// Add assistant message to chat
			this.addMessage("assistant", response.text, response.code);

			// Hide loading indicator
			this._view?.webview.postMessage({ command: "showLoading", value: false });
		} catch (error) {
			// Hide loading indicator
			this._view?.webview.postMessage({ command: "showLoading", value: false });

			// Show error message
			this.addMessage("assistant", `Error: ${error.message}`);
		}
	}

	private _updateWebview() {
		if (this._view) {
			this._view.webview.postMessage({
				command: "updateMessages",
				messages: this._messages,
			});
		}
	}

	private _insertCodeToEditor(code: string) {
		const editor = vscode.window.activeTextEditor;
		if (editor) {
			editor.edit((editBuilder) => {
				editBuilder.insert(editor.selection.active, code);
			});
		}
	}

	private _getHtmlForWebview(webview: vscode.Webview) {
		// Create URIs for scripts and styles
		const scriptUri = webview.asWebviewUri(
			vscode.Uri.joinPath(this._extensionUri, "media", "main.js"),
		);
		const styleUri = webview.asWebviewUri(
			vscode.Uri.joinPath(this._extensionUri, "media", "main.css"),
		);

		// Use a nonce to allow only specific scripts to be run
		const nonce = this._getNonce();

		return `<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
      <link href="${styleUri}" rel="stylesheet">
      <title>Codegen Chat</title>
    </head>
    <body>
      <div id="chat-container">
        <div id="messages"></div>
        <div id="input-container">
          <textarea id="message-input" placeholder="Ask Codegen a question..."></textarea>
          <button id="send-button">Send</button>
        </div>
        <div id="loading" class="hidden">
          <div class="spinner"></div>
        </div>
      </div>
      <script nonce="${nonce}" src="${scriptUri}"></script>
    </body>
    </html>`;
	}

	private _getNonce() {
		let text = "";
		const possible =
			"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
		for (let i = 0; i < 32; i++) {
			text += possible.charAt(Math.floor(Math.random() * possible.length));
		}
		return text;
	}
}
