import type { ICredentialType, INodeProperties } from "n8n-workflow";

export class CodegenApi implements ICredentialType {
	name = "codegenApi";
	displayName = "Codegen API";
	documentationUrl = "https://docs.codegen.com/introduction/api";
	properties: INodeProperties[] = [
		{
			displayName: "API Token",
			name: "apiToken",
			type: "string",
			typeOptions: {
				password: true,
			},
			default: "",
			required: true,
			description: "The API token for Codegen API authentication",
		},
	];
}
