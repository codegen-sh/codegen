import * as vscode from "vscode";

/**
 * Get the selected text from the editor
 */
export function getSelectedText(editor: vscode.TextEditor): string {
	const selection = editor.selection;
	if (selection.isEmpty) {
		return "";
	}
	return editor.document.getText(selection);
}

/**
 * Get the language of the document
 */
export function getDocumentLanguage(document: vscode.TextDocument): string {
	return document.languageId;
}

/**
 * Insert text at the current cursor position
 */
export function insertText(editor: vscode.TextEditor, text: string): void {
	const selection = editor.selection;
	editor.edit((editBuilder) => {
		editBuilder.insert(selection.active, text);
	});
}

/**
 * Get the current file path
 */
export function getCurrentFilePath(): string | undefined {
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		return undefined;
	}
	return editor.document.uri.fsPath;
}

/**
 * Get the current workspace folder
 */
export function getCurrentWorkspaceFolder():
	| vscode.WorkspaceFolder
	| undefined {
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		return undefined;
	}
	return vscode.workspace.getWorkspaceFolder(editor.document.uri);
}

/**
 * Get the current project name
 */
export function getCurrentProjectName(): string | undefined {
	const workspaceFolder = getCurrentWorkspaceFolder();
	if (!workspaceFolder) {
		return undefined;
	}
	return workspaceFolder.name;
}

/**
 * Get the current file name
 */
export function getCurrentFileName(): string | undefined {
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		return undefined;
	}
	return editor.document.fileName.split(/[\\/]/).pop();
}

/**
 * Get the current line of code
 */
export function getCurrentLine(editor: vscode.TextEditor): string {
	const position = editor.selection.active;
	const line = editor.document.lineAt(position.line);
	return line.text;
}

/**
 * Get the current function or class
 * This is a simple implementation and might not work for all languages
 */
export function getCurrentFunction(
	editor: vscode.TextEditor,
): string | undefined {
	const document = editor.document;
	const position = editor.selection.active;

	// Simple implementation - search backwards for function or class definition
	for (let i = position.line; i >= 0; i--) {
		const line = document.lineAt(i).text.trim();
		if (
			line.startsWith("function ") ||
			line.startsWith("class ") ||
			line.startsWith("def ") ||
			line.match(/^[a-zA-Z0-9_]+\s*\([^)]*\)\s*{/)
		) {
			return line;
		}
	}

	return undefined;
}
