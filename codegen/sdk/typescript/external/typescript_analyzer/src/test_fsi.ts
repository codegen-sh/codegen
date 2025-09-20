import * as ts from "typescript";
import { TypeScriptAnalyzer } from "./analyzer";
import { ProxyFileSystem } from "./fs_proxy";

class MockTestFileSystem extends ProxyFileSystem {
	constructor() {
		super();

		// Add a mock tsconfig.json with all required fields
		this.addFile(
			"/tsconfig.json",
			JSON.stringify({
				compilerOptions: {
					target: "ES2020",
					module: "ES2020",
					strict: true,
					esModuleInterop: true,
					skipLibCheck: true,
					forceConsistentCasingInFileNames: true,
				},
				files: ["test.ts"],
				include: ["**/*"],
				exclude: ["node_modules"],
			}),
		);

		// Add typescript lib files that might be needed
		this.addFile("/lib.es2020.d.ts", ""); // Empty placeholder
		this.addFile("/lib.dom.d.ts", ""); // Empty placeholder
		this.addFile("/lib.dom.iterable.d.ts", ""); // Empty placeholder

		// Add a sample TypeScript file
		this.addFile(
			"/src/test.ts",
			`
            export function basicFunction(x: number): string {
                return x.toString();
            }

            export const arrowFunction = (y: string): number => {
                return parseInt(y);
            };

            export class TestClass {
                classMethod(z: boolean): void {
                    console.log(z);
                }
            }
        `,
		);
	}
}

async function runTests() {
	console.log("Starting FileSystemInterface tests...\n");

	const mockFS = new MockTestFileSystem();
	mockFS.debugPrintFiles();

	try {
		console.log("\nCreating TypeScriptAnalyzer with mock file system...");
		const analyzer = new TypeScriptAnalyzer("/", mockFS);

		console.log("\nTesting getAllFunctionsInProject():");
		const functions = analyzer.getAllFunctionsInProject();
		console.log(`Found ${functions.length} functions:`);
		for (const func of functions) {
			console.log(`- ${func.name} (${func.kind})`);
			console.log(`  Return type: ${func.returnType}`);
			console.log(`  Parameters: ${func.parameters}\n`);
		}

		console.log("Testing getFunctionAtPosition():");
		const fileContent = mockFS.readFile("/src/test.ts") || "";
		const positions = [
			{ pos: fileContent.indexOf("basicFunction"), desc: "basicFunction" },
			{ pos: fileContent.indexOf("arrowFunction"), desc: "arrowFunction" },
			{ pos: fileContent.indexOf("classMethod"), desc: "classMethod" },
		];

		for (const { pos, desc } of positions) {
			if (pos === -1) {
				console.log(`Could not find position for ${desc}`);
				continue;
			}
			try {
				const returnType = analyzer.getFunctionAtPosition(
					"/src/test.ts",
					pos + 20,
				);
				console.log(`- ${desc} return type: ${returnType}`);
			} catch (error) {
				console.error(`- Error getting return type for ${desc}:`, error);
			}
		}
	} catch (error) {
		console.error("Test failed:", error);
		console.error("Full error:", error instanceof Error ? error.stack : error);
		process.exit(1);
	}
}

runTests().catch(console.error);
