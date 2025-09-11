export interface FileSystemInterface {
	readFile: (path: string) => string | undefined;
	writeFile?: (path: string, data: string) => void;
	readDirectory?: (path: string) => string[];
	getDirectories?: (path: string) => string[];
	fileExists: (path: string) => boolean;
}
