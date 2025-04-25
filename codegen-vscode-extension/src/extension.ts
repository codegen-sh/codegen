import * as vscode from "vscode";
import { CodegenAPI } from "./api/codegenAPI";
import { registerCommands } from "./commands";
import { ChatViewProvider } from "./providers/chatViewProvider";

export function activate(context: vscode.ExtensionContext) {
	console.log("Codegen extension is now active!");

	// Initialize the API client
	const api = new CodegenAPI();

	// Register the chat view provider
	const chatViewProvider = new ChatViewProvider(context.extensionUri, api);
	context.subscriptions.push(
		vscode.window.registerWebviewViewProvider(
			"codegen.chatView",
			chatViewProvider,
			{ webviewOptions: { retainContextWhenHidden: true } },
		),
	);

	// Register commands
	registerCommands(context, api, chatViewProvider);

	// Status bar item
	const statusBarItem = vscode.window.createStatusBarItem(
		vscode.StatusBarAlignment.Right,
		100,
	);
	statusBarItem.text = "$(sparkle) Codegen";
	statusBarItem.tooltip = "Codegen AI Assistant";
	statusBarItem.command = "codegen.askQuestion";
	statusBarItem.show();
	context.subscriptions.push(statusBarItem);
}

export function deactivate() {
	// Clean up resources
}
