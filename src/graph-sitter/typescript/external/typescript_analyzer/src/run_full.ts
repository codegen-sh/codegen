import * as fs from "node:fs";
import * as path from "node:path";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import { type FunctionInfo, TypeScriptAnalyzer } from "./analyzer";

interface FunctionAnalysis {
	name: string;
	returnType: string;
	parameters?: string;
	kind?: string;
}

interface FileAnalysis {
	relativePath: string;
	functions: { [functionName: string]: FunctionAnalysis };
}

interface AnalyzerOutput {
	projectPath: string;
	analysisDate: string;
	files: { [filePath: string]: FileAnalysis };
	summary: {
		totalFiles: number;
		totalFunctions: number;
	};
}

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
	.option("project", {
		alias: "p",
		type: "string",
		description: "Path to the TypeScript project",
		demandOption: true,
	})
	.option("output", {
		alias: "o",
		type: "string",
		description: "Output JSON file path",
		default: "typescript-analysis.json",
	})
	.option("minimal", {
		alias: "m",
		type: "boolean",
		description: "Output only function names and return types",
		default: false,
	})
	.option("pretty", {
		type: "boolean",
		description: "Pretty print JSON output",
		default: true,
	})
	.help()
	.parseSync();

function groupFunctionsByFile(
	functions: FunctionInfo[],
	projectPath: string,
	minimal: boolean,
): AnalyzerOutput["files"] {
	const files: AnalyzerOutput["files"] = {};

	for (const func of functions) {
		const relativePath = path.relative(projectPath, func.filePath);

		if (!files[func.filePath]) {
			files[func.filePath] = {
				relativePath,
				functions: {},
			};
		}

		const functionAnalysis: FunctionAnalysis = {
			name: func.name,
			returnType: func.returnType,
			...(minimal
				? {}
				: {
						parameters: func.parameters,
						kind: func.kind,
					}),
		};

		files[func.filePath].functions[func.name] = functionAnalysis;
	}

	return files;
}

async function main() {
	try {
		// Resolve absolute paths
		const projectPath = path.resolve(argv.project as string);
		const outputPath = path.resolve(argv.output as string);

		console.log(`Analyzing TypeScript project at: ${projectPath}`);

		// Create analyzer instance
		const analyzer = new TypeScriptAnalyzer(projectPath);

		// Get all functions
		const functions = analyzer.getAllFunctionsInProject();

		// Group functions by file
		const groupedFiles = groupFunctionsByFile(
			functions,
			projectPath,
			argv.minimal as boolean,
		);

		// Prepare output data
		const output: AnalyzerOutput = {
			projectPath,
			analysisDate: new Date().toISOString(),
			files: groupedFiles,
			summary: {
				totalFiles: Object.keys(groupedFiles).length,
				totalFunctions: functions.length,
			},
		};

		// Write to file
		fs.writeFileSync(
			outputPath,
			JSON.stringify(output, null, argv.pretty ? 2 : 0),
		);

		console.log("\nAnalysis complete!");
		console.log(`Output written to: ${outputPath}`);
		console.log("\nSummary:");
		console.log(`- Total files analyzed: ${output.summary.totalFiles}`);
		console.log(`- Total functions found: ${output.summary.totalFunctions}`);
	} catch (error) {
		console.error("Error during analysis:", error);
		process.exit(1);
	}
}

main();
