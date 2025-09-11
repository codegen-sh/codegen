import * as ts from "typescript";
import type { FileSystemInterface } from "./fsi";

function resolvePath(p: string): string {
	// Simple resolve that just returns the path as-is
	// In a real implementation this would handle .. and . segments
	return p;
}

function getDirname(p: string): string {
	// Simple dirname that returns everything before the last /
	const lastSlash = p.lastIndexOf("/");
	if (lastSlash === -1) return ".";
	return p.slice(0, lastSlash);
}

const TYPE_FORMAT_FLAGS = ts.TypeFormatFlags.NoTruncation;

export interface FunctionInfo {
	name: string;
	returnType: string;
	parameters: string;
	kind: string;
	filePath: string; // Added to track which file the function is from
}

export class TypeScriptAnalyzer {
	private program: ts.Program;
	private typeChecker: ts.TypeChecker;

	constructor(projectPath: string, fileSystem?: FileSystemInterface) {
		// Create a custom compiler host if custom file system functions are provided
		const compilerHost: ts.CompilerHost = fileSystem
			? {
					getSourceFile: (
						fileName: string,
						languageVersion: ts.ScriptTarget,
						onError?: (message: string) => void,
					) => {
						const sourceText = fileSystem.readFile(fileName);
						return sourceText
							? ts.createSourceFile(fileName, sourceText, languageVersion)
							: undefined;
					},
					getDefaultLibFileName: (defaultLibOptions: ts.CompilerOptions) =>
						`/${ts.getDefaultLibFileName(defaultLibOptions)}`,
					writeFile: fileSystem.writeFile || (() => {}),
					getCurrentDirectory: () => "/",
					getDirectories: fileSystem.getDirectories || (() => []),
					readDirectory: fileSystem.readDirectory || (() => []),
					fileExists: (fileName: string) => fileSystem.fileExists(fileName),
					readFile: (fileName: string) => fileSystem.readFile(fileName),
					getCanonicalFileName: (fileName: string) => fileName,
					useCaseSensitiveFileNames: () => true,
					getNewLine: () => "\n",
					getEnvironmentVariable: () => "",
				}
			: ts.createCompilerHost({});

		// Create a custom parse config host
		const parseConfigHost: ts.ParseConfigHost = {
			useCaseSensitiveFileNames: true,
			readDirectory: (
				path: string,
				extensions?: readonly string[],
				exclude?: readonly string[],
				include?: readonly string[],
				depth?: number,
			) => {
				return fileSystem
					? fileSystem.readDirectory?.(path) || []
					: ts.sys.readDirectory(path, extensions, exclude, include, depth);
			},
			fileExists: fileSystem ? fileSystem.fileExists : ts.sys.fileExists,
			readFile: fileSystem ? fileSystem.readFile : ts.sys.readFile,
		};

		// Find the base tsconfig.json file
		const baseConfigPath = ts.findConfigFile(
			projectPath,
			fileSystem ? fileSystem.fileExists : ts.sys.fileExists,
			"tsconfig.json",
		);

		if (!baseConfigPath) {
			throw new Error("Could not find a valid 'tsconfig.json'.");
		}

		// Parse the base config file
		const baseConfig = ts.readConfigFile(
			baseConfigPath,
			fileSystem ? fileSystem.readFile : ts.sys.readFile,
		);

		if (baseConfig.error) {
			throw new Error(
				`Error reading tsconfig.json: ${baseConfig.error.messageText}`,
			);
		}
		// Parse the config content
		const parsedConfig = ts.parseJsonConfigFileContent(
			baseConfig.config,
			parseConfigHost,
			projectPath,
		);

		// Find all tsconfig files and parse them
		const allConfigPaths = this.findTsConfigFiles(projectPath, fileSystem);
		const allFileNames = new Set(parsedConfig.fileNames);

		// Add files from each config
		for (const configPath of allConfigPaths) {
			if (configPath === baseConfigPath) continue;

			const config = ts.readConfigFile(
				configPath,
				fileSystem ? fileSystem.readFile : ts.sys.readFile,
			);
			if (!config.error) {
				const parsed = ts.parseJsonConfigFileContent(
					config.config,
					parseConfigHost,
					getDirname(configPath),
				);
				for (const f of parsed.fileNames) {
					allFileNames.add(f);
				}
			}
		}

		// Create program with custom host if provided
		this.program = ts.createProgram({
			rootNames: Array.from(allFileNames),
			options: parsedConfig.options,
			host: compilerHost,
		});
		this.typeChecker = this.program.getTypeChecker();
	}

	private findTsConfigFiles(
		projectPath: string,
		fileSystem?: FileSystemInterface,
	): string[] {
		const tsconfigPaths: string[] = [];
		const readDirectory = fileSystem
			? fileSystem.readDirectory
			: ts.sys.readDirectory;

		// Get all files recursively from the directory
		const entries = readDirectory?.(projectPath) || [];

		// Filter for tsconfig.json files, excluding node_modules and hidden directories
		for (const entry of entries) {
			if (
				entry.includes("node_modules") ||
				entry.split("/").some((part) => part.startsWith("."))
			) {
				continue;
			}

			if (entry.endsWith("/tsconfig.json")) {
				tsconfigPaths.push(entry);
			}
		}

		return tsconfigPaths;
	}

	getFunctionAtPosition(filePath: string, position: number): string {
		const resolvedPath = resolvePath(filePath);
		const sourceFile = this.program.getSourceFile(resolvedPath);

		if (!sourceFile) {
			throw new Error(`Could not find source file: ${filePath}`);
		}

		// Find the node at the exact position
		function findNodeAtPosition(node: ts.Node): ts.Node | undefined {
			if (position >= node.getStart() && position < node.getEnd()) {
				// Check children first to get the most specific node
				let matchingChild: ts.Node | undefined;
				ts.forEachChild(node, (child) => {
					const foundNode = findNodeAtPosition(child);
					if (foundNode) {
						matchingChild = foundNode;
					}
				});
				return matchingChild || node;
			}
			return undefined;
		}

		// Enhanced findContainingFunction to handle arrow functions
		function findContainingFunction(node: ts.Node): ts.Node | undefined {
			if (!node) return undefined;

			// Check if the node itself is a function-like declaration
			if (ts.isFunctionLike(node)) {
				return node;
			}

			// Handle variable declarations with arrow functions
			if (ts.isVariableDeclaration(node)) {
				const initializer = node.initializer;
				if (initializer && ts.isArrowFunction(initializer)) {
					return initializer;
				}
			}

			// Handle property assignments with arrow functions
			if (ts.isPropertyAssignment(node)) {
				const initializer = node.initializer;
				if (initializer && ts.isArrowFunction(initializer)) {
					return initializer;
				}
			}

			// Handle binary expressions (e.g., assignments) with arrow functions
			if (ts.isBinaryExpression(node)) {
				const right = node.right;
				if (right && ts.isArrowFunction(right)) {
					return right;
				}
			}

			// Recursively check parent nodes
			return node.parent ? findContainingFunction(node.parent) : undefined;
		}

		// Find the node at position and its containing function
		const nodeAtPosition = findNodeAtPosition(sourceFile);
		if (!nodeAtPosition) {
			throw new Error(`No node found at position ${position}`);
		}

		const containingFunction = findContainingFunction(nodeAtPosition);
		if (!containingFunction) {
			throw new Error(`No function found at position ${position}`);
		}

		// Get the function's return type
		if (
			ts.isArrowFunction(containingFunction) ||
			ts.isFunctionLike(containingFunction)
		) {
			// Try to get the signature directly first
			const signature = this.typeChecker.getSignatureFromDeclaration(
				containingFunction as ts.SignatureDeclaration,
			);

			if (signature) {
				const returnType = this.typeChecker.getReturnTypeOfSignature(signature);
				return this.typeChecker.typeToString(
					returnType,
					undefined,
					TYPE_FORMAT_FLAGS,
				);
			}

			// If no direct signature, try to get it from the type
			const type = this.typeChecker.getTypeAtLocation(containingFunction);
			const signatures = this.typeChecker.getSignaturesOfType(
				type,
				ts.SignatureKind.Call,
			);

			if (signatures.length > 0) {
				const returnType = this.typeChecker.getReturnTypeOfSignature(
					signatures[0],
				);
				return this.typeChecker.typeToString(
					returnType,
					undefined,
					TYPE_FORMAT_FLAGS,
				);
			}
		}

		throw new Error("Could not determine function return type");
	}

	private getParameterTypesString(node: ts.SignatureDeclaration): string {
		return `(${node.parameters
			.map((param) => {
				const paramType = this.typeChecker.getTypeAtLocation(param);
				return `${param.name.getText()}: ${this.typeChecker.typeToString(paramType, undefined, TYPE_FORMAT_FLAGS)}`;
			})
			.join(", ")})`;
	}

	private getFunctionKind(node: ts.Node): string {
		if (ts.isFunctionDeclaration(node)) return "function";
		if (ts.isArrowFunction(node)) return "arrow function";
		if (ts.isMethodDeclaration(node)) return "method";
		if (ts.isFunctionExpression(node)) return "function expression";
		return "unknown";
	}

	private getNodeReturnType(node: ts.Node): string {
		const signature = this.typeChecker.getSignatureFromDeclaration(
			node as ts.SignatureDeclaration,
		);

		if (signature) {
			const returnType = this.typeChecker.getReturnTypeOfSignature(signature);
			return this.typeChecker.typeToString(
				returnType,
				undefined,
				TYPE_FORMAT_FLAGS,
			);
		}

		const type = this.typeChecker.getTypeAtLocation(node);
		const signatures = this.typeChecker.getSignaturesOfType(
			type,
			ts.SignatureKind.Call,
		);
		if (signatures.length > 0) {
			const returnType = this.typeChecker.getReturnTypeOfSignature(
				signatures[0],
			);
			return this.typeChecker.typeToString(
				returnType,
				undefined,
				TYPE_FORMAT_FLAGS,
			);
		}

		return "unknown";
	}

	private analyzeFunctionsInFile(sourceFile: ts.SourceFile): FunctionInfo[] {
		const functions: FunctionInfo[] = [];
		const filePath = sourceFile.fileName;

		const visit = (node: ts.Node) => {
			// Handle function declarations
			if (ts.isFunctionDeclaration(node) && node.name) {
				functions.push({
					name: node.name.getText(),
					returnType: this.getNodeReturnType(node),
					parameters: this.getParameterTypesString(node),
					kind: "function",
					filePath,
				});
			}
			// Handle arrow functions and function expressions in variable declarations
			else if (ts.isVariableStatement(node)) {
				for (const declaration of node.declarationList.declarations) {
					if (ts.isVariableDeclaration(declaration) && declaration.name) {
						const initializer = declaration.initializer;
						if (
							initializer &&
							(ts.isArrowFunction(initializer) ||
								ts.isFunctionExpression(initializer))
						) {
							functions.push({
								name: declaration.name.getText(),
								returnType: this.getNodeReturnType(initializer),
								parameters: this.getParameterTypesString(initializer),
								kind: this.getFunctionKind(initializer),
								filePath,
							});
						}
					}
				}
			}
			// Handle class methods
			else if (ts.isMethodDeclaration(node) && node.name) {
				const parentClass = node.parent;
				const className =
					ts.isClassDeclaration(parentClass) && parentClass.name
						? `${parentClass.name.getText()}.`
						: "";
				functions.push({
					name: className + node.name.getText(),
					returnType: this.getNodeReturnType(node),
					parameters: this.getParameterTypesString(node),
					kind: "method",
					filePath,
				});
			}

			ts.forEachChild(node, visit);
		};

		ts.forEachChild(sourceFile, visit);
		return functions;
	}

	getAllFunctionsInProject(): FunctionInfo[] {
		const functions: FunctionInfo[] = [];

		// Get all source files from the program
		const sourceFiles = this.program.getSourceFiles();

		// Filter out declaration files and analyze each source file
		for (const sourceFile of sourceFiles) {
			if (
				!sourceFile.isDeclarationFile &&
				!sourceFile.fileName.includes("node_modules")
			) {
				const fileFunctions = this.analyzeFunctionsInFile(sourceFile);
				functions.push(...fileFunctions);
			}
		}

		return functions;
	}
}
