import path from "node:path";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import { TypeScriptAnalyzer } from "./analyzer.js";

function parseArgs() {
	return yargs(hideBin(process.argv))
		.option("project", {
			alias: "p",
			type: "string",
			description: "Path to the TypeScript project root",
			demandOption: true,
		})
		.option("file", {
			alias: "f",
			type: "string",
			description: "Path to the specific TypeScript file",
			demandOption: true,
		})
		.option("position", {
			alias: "pos",
			type: "number",
			description: "Byte position in the file",
			demandOption: true,
		})
		.help()
		.parseSync();
}

function main() {
	try {
		const argv = parseArgs();
		const projectPath = path.resolve(argv.project);
		const filePath = path.resolve(argv.file);
		const position = argv.position;

		// Create analyzer instance
		const analyzer = new TypeScriptAnalyzer(projectPath);

		try {
			// Get return type at position
			const returnType = analyzer.getFunctionAtPosition(filePath, position);
			// Print only the return type, nothing else
			console.log(returnType);
		} catch (error) {
			// Print just the error message without any formatting
			console.error(error instanceof Error ? error.message : "Unknown error");
			process.exit(1);
		}
	} catch (error) {
		// Handle project initialization errors
		console.error(error instanceof Error ? error.message : "Unknown error");
		process.exit(1);
	}
}

main();
