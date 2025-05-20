module.exports = {
	packageName: "n8n-nodes-codegen",
	nodeTypes: {
		Codegen: {
			sourcePath: "./dist/nodes/Codegen/Codegen.node.js",
			type: "Codegen",
		},
	},
	credentialTypes: {
		CodegenApi: {
			sourcePath: "./dist/credentials/CodegenApi.credentials.js",
			type: "CodegenApi",
		},
	},
};
