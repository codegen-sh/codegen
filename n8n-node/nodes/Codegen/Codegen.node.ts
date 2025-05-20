import axios from "axios";
import type { IExecuteFunctions } from "n8n-core";
import {
	type INodeExecutionData,
	type INodeType,
	type INodeTypeDescription,
	NodeOperationError,
} from "n8n-workflow";

export class Codegen implements INodeType {
	description: INodeTypeDescription = {
		displayName: "Codegen",
		name: "codegen",
		icon: "file:codegen.svg",
		group: ["transform"],
		version: 1,
		subtitle: '={{$parameter["operation"] + ": " + $parameter["resource"]}}',
		description: "Interact with the Codegen API",
		defaults: {
			name: "Codegen",
		},
		inputs: ["main"],
		outputs: ["main"],
		credentials: [
			{
				name: "codegenApi",
				required: true,
			},
		],
		properties: [
			{
				displayName: "Resource",
				name: "resource",
				type: "options",
				noDataExpression: true,
				options: [
					{
						name: "Agent",
						value: "agent",
					},
				],
				default: "agent",
			},
			{
				displayName: "Operation",
				name: "operation",
				type: "options",
				noDataExpression: true,
				displayOptions: {
					show: {
						resource: ["agent"],
					},
				},
				options: [
					{
						name: "Run",
						value: "run",
						description: "Run a Codegen agent task",
						action: "Run a Codegen agent task",
					},
					{
						name: "Ask Expert",
						value: "askExpert",
						description: "Ask the Codegen expert system a question",
						action: "Ask the Codegen expert system a question",
					},
					{
						name: "Create Codemod",
						value: "createCodemod",
						description: "Create a new codemod",
						action: "Create a new codemod",
					},
				],
				default: "run",
			},
			// Fields for Run operation
			{
				displayName: "Function Name",
				name: "functionName",
				type: "string",
				default: "",
				required: true,
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["run"],
					},
				},
				description: "Name of the function or codemod to run",
			},
			{
				displayName: "Repository Full Name",
				name: "repoFullName",
				type: "string",
				default: "",
				required: true,
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["run"],
					},
				},
				description: "Full name of the repository (e.g., owner/repo)",
			},
			{
				displayName: "Run Type",
				name: "runType",
				type: "options",
				options: [
					{
						name: "Diff",
						value: "diff",
					},
					{
						name: "PR",
						value: "pr",
					},
				],
				default: "diff",
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["run"],
					},
				},
				description: "Type of run (diff or PR)",
			},
			{
				displayName: "Include Source",
				name: "includeSource",
				type: "boolean",
				default: true,
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["run"],
					},
				},
				description: "Whether to include the source code in the request",
			},
			{
				displayName: "Source Code",
				name: "sourceCode",
				type: "string",
				typeOptions: {
					rows: 10,
				},
				default: "",
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["run"],
						includeSource: [true],
					},
				},
				description: "Source code of the function or codemod",
			},
			{
				displayName: "Template Context",
				name: "templateContext",
				type: "json",
				default: "{}",
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["run"],
					},
				},
				description: "Context variables to pass to the codemod",
			},
			// Fields for Ask Expert operation
			{
				displayName: "Query",
				name: "query",
				type: "string",
				default: "",
				required: true,
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["askExpert"],
					},
				},
				description: "The question to ask the expert system",
			},
			// Fields for Create Codemod operation
			{
				displayName: "Name",
				name: "name",
				type: "string",
				default: "",
				required: true,
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["createCodemod"],
					},
				},
				description: "Name for the new codemod",
			},
			{
				displayName: "Query",
				name: "createQuery",
				type: "string",
				default: "",
				required: true,
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["createCodemod"],
					},
				},
				description: "Description of what the codemod should do",
			},
			{
				displayName: "Language",
				name: "language",
				type: "options",
				options: [
					{
						name: "Python",
						value: "python",
					},
					{
						name: "TypeScript",
						value: "typescript",
					},
					{
						name: "JavaScript",
						value: "javascript",
					},
				],
				default: "python",
				displayOptions: {
					show: {
						resource: ["agent"],
						operation: ["createCodemod"],
					},
				},
				description: "Programming language for the codemod",
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		// Get credentials
		const credentials = await this.getCredentials("codegenApi");
		const apiToken = credentials.apiToken as string;

		// For each item
		for (let i = 0; i < items.length; i++) {
			try {
				const resource = this.getNodeParameter("resource", i) as string;
				const operation = this.getNodeParameter("operation", i) as string;

				let responseData;

				if (resource === "agent") {
					// Endpoints from the Codegen API
					const endpoints = {
						run: "https://api.codegen.com/run",
						askExpert: "https://api.codegen.com/expert",
						createCodemod: "https://api.codegen.com/create",
					};

					// Set up headers with authentication
					const headers = {
						Authorization: `Bearer ${apiToken}`,
						"Content-Type": "application/json",
					};

					if (operation === "run") {
						const functionName = this.getNodeParameter(
							"functionName",
							i,
						) as string;
						const repoFullName = this.getNodeParameter(
							"repoFullName",
							i,
						) as string;
						const runType = this.getNodeParameter("runType", i) as string;
						const includeSource = this.getNodeParameter(
							"includeSource",
							i,
						) as boolean;
						const templateContext = JSON.parse(
							this.getNodeParameter("templateContext", i) as string,
						);

						const requestData: any = {
							input: {
								codemod_name: functionName,
								repo_full_name: repoFullName,
								codemod_run_type: runType,
								template_context: templateContext,
							},
						};

						if (includeSource) {
							const sourceCode = this.getNodeParameter(
								"sourceCode",
								i,
							) as string;
							requestData.input.codemod_source = sourceCode;
						}

						// Make API request
						const response = await axios.post(endpoints.run, requestData, {
							headers,
						});
						responseData = response.data;
					} else if (operation === "askExpert") {
						const query = this.getNodeParameter("query", i) as string;

						const requestData = {
							input: {
								query,
							},
						};

						// Make API request
						const response = await axios.get(endpoints.askExpert, {
							headers,
							params: requestData,
						});
						responseData = response.data;
					} else if (operation === "createCodemod") {
						const name = this.getNodeParameter("name", i) as string;
						const query = this.getNodeParameter("createQuery", i) as string;
						const language = this.getNodeParameter("language", i) as string;

						const requestData = {
							input: {
								name,
								query,
								language,
							},
						};

						// Make API request
						const response = await axios.get(endpoints.createCodemod, {
							headers,
							params: requestData,
						});
						responseData = response.data;
					} else {
						throw new NodeOperationError(
							this.getNode(),
							`The operation "${operation}" is not supported!`,
						);
					}
				}

				// Return the response data
				const executionData = this.helpers.constructExecutionMetaData(
					this.helpers.returnJsonArray(responseData),
					{ itemData: { item: i } },
				);
				returnData.push(...executionData);
			} catch (error) {
				if (this.continueOnFail()) {
					const executionData = this.helpers.constructExecutionMetaData(
						this.helpers.returnJsonArray({ error: error.message }),
						{ itemData: { item: i } },
					);
					returnData.push(...executionData);
					continue;
				}
				throw error;
			}
		}

		return [returnData];
	}
}
