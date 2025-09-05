import { builtinModules } from "node:module";
import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";

export default {
	input: "src/index.ts",
	output: {
		file: "dist/index.js",
		format: "cjs",
		sourcemap: false,
	},
	// Only exclude Node.js built-in modules that can't be bundled
	external: builtinModules,
	plugins: [
		// Resolve node_modules dependencies
		resolve({
			preferBuiltins: false,
			mainFields: ["module", "main"],
			// Bundle node_modules content
			modulesOnly: false,
		}),
		// Convert CommonJS modules to ES6
		commonjs({
			ignoreTryCatch: true,
			// Include node_modules
			include: /node_modules/,
		}),
		// Handle TypeScript
		typescript({
			tsconfig: "./tsconfig.json",
			declaration: true,
			declarationDir: "dist",
		}),
	],
};
