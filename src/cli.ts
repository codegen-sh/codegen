import { Command } from "commander";
import { version } from "../package.json";
import { configCommand } from "./cli/commands/config";
import { createCommand } from "./cli/commands/create";
import { deployCommand } from "./cli/commands/deploy";
import { expertCommand } from "./cli/commands/expert";
import { initCommand } from "./cli/commands/init";
import { listCommand } from "./cli/commands/list";
import { loginCommand } from "./cli/commands/login";
import { logoutCommand } from "./cli/commands/logout";
import { lspCommand } from "./cli/commands/lsp";
import { notebookCommand } from "./cli/commands/notebook";
import { profileCommand } from "./cli/commands/profile";
import { resetCommand } from "./cli/commands/reset";
import { runCommand } from "./cli/commands/run";
import { runOnPrCommand } from "./cli/commands/run-on-pr";
import { serveCommand } from "./cli/commands/serve";
import { startCommand } from "./cli/commands/start";
import { styleDebugCommand } from "./cli/commands/style-debug";
import { updateCommand } from "./cli/commands/update";

export async function main(): Promise<void> {
	const program = new Command();

	program.version(version, "-v, --version", "Output the current version");
	program.name("codegen");

	// Register commands
	program.addCommand(configCommand());
	program.addCommand(createCommand());
	program.addCommand(deployCommand());
	program.addCommand(expertCommand());
	program.addCommand(initCommand());
	program.addCommand(listCommand());
	program.addCommand(loginCommand());
	program.addCommand(logoutCommand());
	program.addCommand(lspCommand());
	program.addCommand(notebookCommand());
	program.addCommand(profileCommand());
	program.addCommand(resetCommand());
	program.addCommand(runCommand());
	program.addCommand(runOnPrCommand());
	program.addCommand(serveCommand());
	program.addCommand(startCommand());
	program.addCommand(styleDebugCommand());
	program.addCommand(updateCommand());

	await program.parseAsync(process.argv);
}
