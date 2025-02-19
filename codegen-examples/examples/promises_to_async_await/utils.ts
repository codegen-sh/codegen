interface QueryResult {
	id: number;
	data: unknown;
}

interface QueryBuilder {
	select(columns: string | string[]): Promise<QueryResult[]>;
}

interface SchemaBuilder {
	hasTable(tableName: string): Promise<boolean>;
}

export function getLockTableName(tableName: string): string {
	return `${tableName}_lock`;
}

export function _createMigrationTable(
	tableName: string,
	schemaName: string,
	trxOrKnex: QueryBuilder,
) {}

export function _createMigrationLockTable(
	lockTable: string,
	schemaName: string,
	trxOrKnex: QueryBuilder,
) {}

export function _insertLockRowIfNeeded(
	tableName: string,
	schemaName: string,
	trxOrKnex: QueryBuilder,
) {}

export function processResult(result: QueryResult) {}

export function functionB(promiseChain: Promise<QueryResult>) {}

export function functionC(promiseChain: Promise<QueryResult>) {}

export async function fetchWithTimeout(id: number, timeout: number) {}

interface Result {
	id: number;
	data?: unknown;
}

export type CallbackFn = (error: Error | null, result?: Result) => void;

export function callback(error: Error | null, result?: Result): void {
	if (error) {
		console.error("Error occurred:", error);
		return;
	}
	console.log("Operation completed successfully:", result);
}

export function getSchemaBuilder(trxOrKnex, schemaName): SchemaBuilder {
	return trxOrKnex.schema.withSchema(schemaName);
}

export function getTable(trxOrKnex, lockTable, schemaName): QueryBuilder {
	// Return the query builder instance
	return trxOrKnex.schema[schemaName].from(lockTable);
}

// Promise creation for usages in the test file
interface UserData {
	id: number;
	name: string;
	email: string;
}

export function fetchUserData(userId: number): Promise<UserData> {
	return new Promise((resolve, reject) => {
		setTimeout(() => {
			if (userId > 0) {
				resolve({
					id: userId,
					name: `User ${userId}`,
					email: `user${userId}@example.com`,
				});
			} else {
				reject(new Error("Invalid user ID"));
			}
		}, 1000);
	});
}

interface Post {
	id: number;
	title: string;
	userId: number;
}

export function fetchUserPosts(userId: number): Promise<Post[]> {
	return new Promise((resolve, reject) => {
		setTimeout(() => {
			if (userId > 0) {
				resolve([
					{ id: 1, title: "Post 1", userId },
					{ id: 2, title: "Post 2", userId },
				]);
			} else {
				reject(new Error("Could not fetch posts"));
			}
		}, 800);
	});
}

interface Comment {
	id: number;
	text: string;
	postId: number;
}

export function fetchPostComments(postId: number): Promise<Comment[]> {
	return new Promise((resolve, reject) => {
		setTimeout(() => {
			if (postId > 0) {
				resolve([
					{ id: 1, text: "Great post!", postId },
					{ id: 2, text: "Thanks for sharing", postId },
				]);
			} else {
				reject(new Error("Could not fetch comments"));
			}
		}, 500);
	});
}

interface RequestOptions {
	url?: string;
	method?: string;
	// biome-ignore lint/suspicious/noExplicitAny: example interface
	body?: any;
}

interface RequestResponse {
	statusCode: number;
	// biome-ignore lint/suspicious/noExplicitAny: example interface
	body: string | any;
}

export function request(opts: RequestOptions): Promise<RequestResponse> {
	return new Promise((resolve) => {
		// Simulated API response
		setTimeout(() => {
			resolve({
				statusCode: 200,
				body: JSON.stringify({ success: true, data: opts }),
			});
		}, 100);
	});
}
