#!/usr/bin/env node

import { main } from "./cli";

main().catch((error) => {
	console.error("Error:", error);
	process.exit(1);
});
