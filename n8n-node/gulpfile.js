const { src, dest } = require("gulp");

// Copies the icon files from the nodes source folders to the dist folder
function copyIcons() {
	return src("./nodes/**/*.svg").pipe(dest("./dist/nodes/"));
}

exports["build:icons"] = copyIcons;
