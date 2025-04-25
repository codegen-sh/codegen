import * as vscode from "vscode";
import type { CodegenAPI } from "./api/codegenAPI";
import type { ChatViewProvider } from "./providers/chatViewProvider";
import { getDocumentLanguage, getSelectedText, insertText } from "./utils";

export function registerCommands(
	context: vscode.ExtensionContext,
	api: CodegenAPI,
	chatViewProvider: ChatViewProvider,
) {
	// Ask a question
	context.subscriptions.push(
		vscode.commands.registerCommand("codegen.askQuestion", async () => {
			const question = await vscode.window.showInputBox({
				prompt: "What would you like to ask Codegen?",
				placeHolder: "Ask a programming question...",
			});

			if (!question) {
				return;
			}

			try {
				vscode.window.withProgress(
					{
						location: vscode.ProgressLocation.Notification,
						title: "Asking Codegen...",
						cancellable: false,
					},
					async (progress) => {
						progress.report({ increment: 0 });

						const response = await api.askQuestion(question);

						progress.report({ increment: 100 });

						// Send to chat view
						chatViewProvider.addMessage("user", question);
						chatViewProvider.addMessage("assistant", response.text);

						// Show the chat view
						vscode.commands.executeCommand("codegen.chatView.focus");

						return response;
					},
				);
			} catch (error) {
				vscode.window.showErrorMessage(`Error: ${error.message}`);
			}
		}),
	);

	// Generate code
	context.subscriptions.push(
		vscode.commands.registerCommand("codegen.generateCode", async () => {
			const prompt = await vscode.window.showInputBox({
				prompt: "Describe the code you want to generate",
				placeHolder: "Generate a function that...",
			});

			if (!prompt) {
				return;
			}

			const editor = vscode.window.activeTextEditor;
			const language = editor
				? getDocumentLanguage(editor.document)
				: undefined;

			try {
				vscode.window.withProgress(
					{
						location: vscode.ProgressLocation.Notification,
						title: "Generating code...",
						cancellable: false,
					},
					async (progress) => {
						progress.report({ increment: 0 });

						const response = await api.generateCode(prompt, language);

						progress.report({ increment: 100 });

						if (editor && response.code) {
							// Insert the generated code at the cursor position
							insertText(editor, response.code);
						}

						// Send to chat view
						chatViewProvider.addMessage("user", `Generate code: ${prompt}`);
						chatViewProvider.addMessage(
							"assistant",
							response.text,
							response.code,
						);

						return response;
					},
				);
			} catch (error) {
				vscode.window.showErrorMessage(`Error: ${error.message}`);
			}
		}),
	);

	// Explain code
	context.subscriptions.push(
		vscode.commands.registerCommand("codegen.explainCode", async () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				vscode.window.showErrorMessage("No active editor");
				return;
			}

			const selectedText = getSelectedText(editor);
			if (!selectedText) {
				vscode.window.showErrorMessage("No code selected");
				return;
			}

			const language = getDocumentLanguage(editor.document);

			try {
				vscode.window.withProgress(
					{
						location: vscode.ProgressLocation.Notification,
						title: "Explaining code...",
						cancellable: false,
					},
					async (progress) => {
						progress.report({ increment: 0 });

						const response = await api.explainCode(selectedText, language);

						progress.report({ increment: 100 });

						// Send to chat view
						chatViewProvider.addMessage(
							"user",
							`Explain this code:\n\`\`\`${language}\n${selectedText}\n\`\`\``,
						);
						chatViewProvider.addMessage("assistant", response.text);

						// Show the chat view
						vscode.commands.executeCommand("codegen.chatView.focus");

						return response;
					},
				);
			} catch (error) {
				vscode.window.showErrorMessage(`Error: ${error.message}`);
			}
		}),
	);

	// Improve code
	context.subscriptions.push(
		vscode.commands.registerCommand("codegen.improveCode", async () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				vscode.window.showErrorMessage("No active editor");
				return;
			}

			const selectedText = getSelectedText(editor);
			if (!selectedText) {
				vscode.window.showErrorMessage("No code selected");
				return;
			}

			const language = getDocumentLanguage(editor.document);

			try {
				vscode.window.withProgress(
					{
						location: vscode.ProgressLocation.Notification,
						title: "Improving code...",
						cancellable: false,
					},
					async (progress) => {
						progress.report({ increment: 0 });

						const response = await api.improveCode(selectedText, language);

						progress.report({ increment: 100 });

						if (response.code) {
							// Show diff and ask if user wants to apply changes
							const document = editor.document;
							const selection = editor.selection;

							const diffEditor =
								await vscode.diff.createTextDocumentAndEditorEdit(
									document,
									selection,
									response.code,
								);

							// Add buttons to apply or discard changes
							const applyChanges = "Apply Changes";
							const discardChanges = "Discard";

							const choice = await vscode.window.showInformationMessage(
								"Review the suggested improvements",
								applyChanges,
								discardChanges,
							);

							if (choice === applyChanges) {
								// Replace the selected text with the improved code
								editor.edit((editBuilder) => {
									editBuilder.replace(selection, response.code || "");
								});
							}
						}

						// Send to chat view
						chatViewProvider.addMessage(
							"user",
							`Improve this code:\n\`\`\`${language}\n${selectedText}\n\`\`\``,
						);
						chatViewProvider.addMessage(
							"assistant",
							response.text,
							response.code,
						);

						return response;
					},
				);
			} catch (error) {
				vscode.window.showErrorMessage(`Error: ${error.message}`);
			}
		}),
	);

	// Fix code
	context.subscriptions.push(
		vscode.commands.registerCommand("codegen.fixCode", async () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				vscode.window.showErrorMessage("No active editor");
				return;
			}

			const selectedText = getSelectedText(editor);
			if (!selectedText) {
				vscode.window.showErrorMessage("No code selected");
				return;
			}

			const language = getDocumentLanguage(editor.document);

			// Ask for error message
			const errorMessage = await vscode.window.showInputBox({
				prompt: "What error are you getting? (optional)",
				placeHolder: "Error message or description of the issue",
			});

			try {
				vscode.window.withProgress(
					{
						location: vscode.ProgressLocation.Notification,
						title: "Fixing code...",
						cancellable: false,
					},
					async (progress) => {
						progress.report({ increment: 0 });

						const response = await api.fixCode(
							selectedText,
							errorMessage,
							language,
						);

						progress.report({ increment: 100 });

						if (response.code) {
							// Show diff and ask if user wants to apply changes
							const document = editor.document;
							const selection = editor.selection;

							const diffEditor =
								await vscode.diff.createTextDocumentAndEditorEdit(
									document,
									selection,
									response.code,
								);

							// Add buttons to apply or discard changes
							const applyChanges = "Apply Changes";
							const discardChanges = "Discard";

							const choice = await vscode.window.showInformationMessage(
								"Review the suggested fixes",
								applyChanges,
								discardChanges,
							);

							if (choice === applyChanges) {
								// Replace the selected text with the fixed code
								editor.edit((editBuilder) => {
									editBuilder.replace(selection, response.code || "");
								});
							}
						}

						// Send to chat view
						const userMessage = errorMessage
							? `Fix this code (error: ${errorMessage}):\n\`\`\`${language}\n${selectedText}\n\`\`\``
							: `Fix this code:\n\`\`\`${language}\n${selectedText}\n\`\`\``;

						chatViewProvider.addMessage("user", userMessage);
						chatViewProvider.addMessage(
							"assistant",
							response.text,
							response.code,
						);

						return response;
					},
				);
			} catch (error) {
				vscode.window.showErrorMessage(`Error: ${error.message}`);
			}
		}),
	);
}
