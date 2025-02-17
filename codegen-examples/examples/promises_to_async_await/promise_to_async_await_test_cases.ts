import {
	_createMigrationLockTable,
	_createMigrationTable,
	_insertLockRowIfNeeded,
	fetchPostComments,
	fetchUserData,
	fetchUserPosts,
	fetchWithTimeout,
	getLockTableName,
	getSchemaBuilder,
	getTable,
} from "./utils";

// ------------------------ Trivial Cases ----------------------------
// 1. Test with one .then
// Input ->
function getValue(): Promise<number> {
	return Promise.resolve(10).then((value) => {
		return value * 2;
	});
}

// Expected:
async function getValueAsync(): Promise<number> {
	const value = await Promise.resolve(10);
	return value * 2;
}
// ------------------------ Challenging Cases ----------------------------

// 2. Example of nested .then() calls with a catch block
function getUserDataAndPosts(userId: number): void {
	fetchUserData(userId)
		.then((user) => {
			console.log("User:", user);
			return fetchUserPosts(user.id);
		})
		.then((posts) => {
			console.log("Posts:", posts);
			return fetchPostComments(posts[0].id);
		})
		.then((comments) => {
			console.log("Comments:", comments);
		})
		.catch((error) => {
			console.error("Error:", error.message);
		});
}

// 4. Promise.all example with assignment of two variables
function getAllUserInfo(userId: number) {
	return Promise.all([fetchUserData(userId), fetchUserPosts(userId)]).then(
		([user, posts]) => {
			return {
				user,
				posts,
			};
		},
	);
}

// 5. Medium length promise chaining with error handling
function processUserData(userId: number): Promise<void> {
	return fetchUserData(userId)
		.then((user) => {
			console.log("Found user:", user);
			return fetchUserPosts(userId);
		})
		.then((posts) => {
			console.log("Found posts:", posts);
			throw new Error("Something went wrong!");
		})
		.then(() => {
			console.log("This will not execute due to the error above");
		})
		.catch((error) => {
			console.error("Caught error:", error.message);
		})
		.finally(() => {
			console.log("Cleanup operations here");
		});
}

async function processUserDataAsync(userId: number): Promise<void> {
	try {
		const user = await fetchUserData(userId);
		console.log("Found user:", user);

		const posts = await fetchUserPosts(userId);
		console.log("Found posts:", posts);

		throw new Error("Something went wrong!");
		console.log("This will not execute due to the error above");
	} catch (error) {
		console.error("Caught error:", error.message);
	} finally {
		console.log("Cleanup operations here");
	}
}

// 6. Example with a long promise chain + catch and finally
function ensureTable(tableName, schemaName, trxOrKnex) {
	const lockTable = getLockTableName(tableName);
	return getSchemaBuilder(trxOrKnex, schemaName)
		.hasTable(tableName)
		.then((exists) => {
			return !exists && _createMigrationTable(tableName, schemaName, trxOrKnex);
		})
		.then(() => {
			return getSchemaBuilder(trxOrKnex, schemaName).hasTable(lockTable);
		})
		.then((exists) => {
			return (
				!exists && _createMigrationLockTable(lockTable, schemaName, trxOrKnex)
			);
		})
		.then(() => {
			return getTable(trxOrKnex, lockTable, schemaName).select("*");
		})
		.then((data) => {
			return (
				!data.length && _insertLockRowIfNeeded(tableName, schemaName, trxOrKnex)
			);
		})
		.then(() => {
			return fetchUserData(1);
		})
		.then(() => {
			return fetchUserPosts(1);
		})
		.then((dataTwo: any) => {
			return fetchPostComments(dataTwo);
		})
		.then(() => {
			return fetchWithTimeout(1, 500);
		})
		.then((dataThree: any) => {
			return fetchUserPosts(dataThree);
		})
		.catch((error) => {
			console.error("Error:", error.message);
		})
		.finally(() => {
			console.log("Cleanup operations here");
		});
}

// Function with complex returns (uses annonymous functions for conversions)
// Input
function create(opts: any): Promise<any> {
	let qResponse = request(opts);
	qResponse = qResponse.then(function success(response) {
		if (response.statusCode < 200 || response.statusCode >= 300) {
			throw new Error(response);
		}
		if (typeof response.body === "string") {
			return JSON.parse(response.body);
		}
		return response.body;
	});

	return qResponse;
}

// Expected
async function createAsync(opts): Promise<any> {
	let qResponse = request(opts);
	const response = await qResponse;
	qResponse = (async (response) => {
		if (response.statusCode < 200 || response.statusCode >= 300) {
			throw new Error(response);
		}
		if (typeof response.body === "string") {
			return JSON.parse(response.body);
		}
		return response.body;
	})(response);

	return qResponse;
}

// 7. Example of handling multiple promises
export function runExamples(): void {
	// Basic nested promises
	getUserDataAndPosts(1);

	// Promise.all
	getAllUserInfo(1)
		.then((info) => console.log("All user info:", info))
		.catch((error) => console.error("Error getting all info:", error));

	// Promise with error handling
	processUserData(1);

	// Promise with timeout
	fetchWithTimeout(1, 2000)
		.then((result) => console.log("Fetched with timeout:", result))
		.catch((error) => console.error("Timeout error:", error.message));
}
