import type { FileSystemInterface } from "./fsi";

export class ProxyFileSystem implements FileSystemInterface {
	public files: Map<string, string> = new Map();

	constructor() {
		// Bind methods to ensure correct 'this' context
		this.setFiles = this.setFiles.bind(this);
		this.fileExists = this.fileExists.bind(this);
		this.readFile = this.readFile.bind(this);
		this.readDirectory = this.readDirectory.bind(this);
		this.getDirectories = this.getDirectories.bind(this);
		this.normalizePath = this.normalizePath.bind(this);
		this.getParentDirectory = this.getParentDirectory.bind(this);
		this.debugPrintFiles = this.debugPrintFiles.bind(this);
	}

	setFiles(files: Map<string, string>): void {
		this.files = files;
	}

	addFile(path: string, content: string): void {
		const normalized = this.normalizePath(path);
		this.files.set(normalized, content);
	}

	readFile = (path: string): string | undefined => {
		const normalized = this.normalizePath(path);
		console.log(`Reading file: ${normalized}`);
		return this.files.get(normalized);
	};

	fileExists = (path: string): boolean => {
		const normalized = this.normalizePath(path);
		console.log(`Checking if file exists: ${normalized}`);

		// Direct file check
		if (this.files.has(normalized)) {
			return true;
		}

		// For tsconfig.json, check parent directories
		if (path.endsWith("tsconfig.json")) {
			let currentDir = normalized;
			while (currentDir !== "/") {
				currentDir = this.getParentDirectory(currentDir);
				const configPath = this.normalizePath(`${currentDir}/tsconfig.json`);
				if (this.files.has(configPath)) {
					return true;
				}
			}
			// Check root
			return this.files.has("/tsconfig.json");
		}

		return false;
	};

	readDirectory = (path: string): string[] => {
		const normalized = this.normalizePath(path);
		console.log(`Reading directory: ${normalized}`);

		const files: string[] = [];
		for (const filePath of this.files.keys()) {
			if (filePath.startsWith(normalized)) {
				files.push(filePath);
			}
		}
		return files;
	};

	getDirectories = (path: string): string[] => {
		const normalized = this.normalizePath(path);
		console.log(`Getting directories under: ${normalized}`);

		const directories = new Set<string>();
		for (const filePath of this.files.keys()) {
			if (filePath.startsWith(normalized)) {
				// Get relative path from the requested directory
				const relativePath = filePath.slice(normalized.length);
				if (relativePath) {
					// Split the relative path and look for directories
					const parts = relativePath.split("/").filter((p) => p);
					if (parts.length > 1) {
						// If there are subdirectories
						directories.add(parts[0]); // Add first subdirectory
					}
				}
			}
		}
		return Array.from(directories);
	};

	protected normalizePath(path: string): string {
		// Remove any './' or multiple slashes and ensure leading slash
		let normalized = path.replace(/\/\.\//g, "/").replace(/\/+/g, "/");
		if (!normalized.startsWith("/")) {
			normalized = `/${normalized}`;
		}
		return normalized;
	}

	protected getParentDirectory(path: string): string {
		const normalized = this.normalizePath(path);
		const lastSlash = normalized.lastIndexOf("/");
		if (lastSlash <= 0) return "/";
		return normalized.slice(0, lastSlash) || "/";
	}

	debugPrintFiles(): void {
		console.log("\nProxy File System Contents:");
		for (const [path, content] of this.files.entries()) {
			console.log(`\nFile: ${path}`);
			console.log(
				"Content:",
				content.slice(0, 100) + (content.length > 100 ? "..." : ""),
			);
		}
	}
}
