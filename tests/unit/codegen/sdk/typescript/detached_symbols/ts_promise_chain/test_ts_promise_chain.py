from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def normalize_whitespace(code: str) -> str:
    """Normalize whitespace in code for comparison.

    1. Removes leading/trailing whitespace from each line
    2. Removes empty lines
    3. Joins lines with a single newline
    """
    return "\n".join(line.strip() for line in code.split("\n") if line.strip())


def test_simple_promise_chain(tmpdir) -> None:
    FILENAME = "simple_promise.ts"
    # language=typescript
    FILE_CONTENT = """
    function getValue(): Promise<number> {
        return Promise.resolve(10).then(value => {
          return value * 2;
        });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_function("getValue")
        promise_chain = function_symbol.promise_chains[0]

        async_await_code = promise_chain.convert_to_async_await(inplace_edit=False)
        expected = """
        let value = await Promise.resolve(10);
        return value * 2;
        """
        assert normalize_whitespace(async_await_code) == normalize_whitespace(expected)


def test_nested_promise_chain_with_catch(tmpdir) -> None:
    FILENAME = "nested_promise.ts"
    # language=typescript
    FILE_CONTENT = """
    function getUserDataAndPosts(userId: number): void {
        fetchUserData(userId)
            .then((user) => {
                console.log('User:', user);
                return fetchUserPosts(user.id);
            })
            .then((posts) => {
                console.log('Posts:', posts);
                return fetchPostComments(posts[0].id);
            })
            .then((comments) => {
                console.log('Comments:', comments);
            })
            .catch((error) => {
                console.error('Error:', error.message);
            });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_function("getUserDataAndPosts")
        promise_chain = function_symbol.promise_chains[0]

        async_await_code = promise_chain.convert_to_async_await(inplace_edit=False)
        expected = """
        try {
            let user = await fetchUserData(userId);
            console.log('User:', user);

            let posts = await fetchUserPosts(user.id);
            console.log('Posts:', posts);

            let comments = await fetchPostComments(posts[0].id);
            console.log('Comments:', comments);
        } catch(error: any) {
            console.error('Error:', error.message);
        }
        """
        assert normalize_whitespace(async_await_code) == normalize_whitespace(expected)


def test_promise_all_with_destructuring(tmpdir) -> None:
    FILENAME = "promise_all.ts"
    # language=typescript
    FILE_CONTENT = """
    function getAllUserInfo(userId: number) {
        return Promise.all([
            fetchUserData(userId),
            fetchUserPosts(userId)
        ])
        .then(([user, posts]) => {
            return {
                user,
                posts
            };
        });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_function("getAllUserInfo")
        promise_chain = function_symbol.promise_chains[0]

        async_await_code = promise_chain.convert_to_async_await(inplace_edit=False)
        expected = """
        let [user, posts] = await Promise.all([
            fetchUserData(userId),
            fetchUserPosts(userId)
        ]);
        return {
            user,
            posts
        };
        """
        assert normalize_whitespace(async_await_code) == normalize_whitespace(expected)


def test_complex_promise_chain_with_catch_finally(tmpdir) -> None:
    FILENAME = "complex_promise.ts"
    # language=typescript
    FILE_CONTENT = """
    function processUserData(userId: number): Promise<void> {
        return fetchUserData(userId)
            .then((user) => {
                console.log('Found user:', user);
                return fetchUserPosts(userId);
            })
            .then((posts) => {
                console.log('Found posts:', posts);
                throw new Error('Something went wrong!');
            })
            .then(() => {
                console.log('This will not execute due to the error above');
            })
            .catch((error) => {
                console.error('Caught error:', error.message);
            })
            .finally(() => {
                console.log('Cleanup operations here');
            });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_function("processUserData")
        promise_chain = function_symbol.promise_chains[0]

        async_await_code = promise_chain.convert_to_async_await(inplace_edit=False)
        expected = """
        try {
        let user = await fetchUserData(userId);
            console.log('Found user:', user);
        let posts = await fetchUserPosts(userId);
            console.log('Found posts:', posts);
        throw new Error('Something went wrong!');
        console.log('This will not execute due to the error above');
        } catch(error: any) {
        console.error('Caught error:', error.message);
        } finally {
        console.log('Cleanup operations here');
        }
        """
        assert normalize_whitespace(async_await_code) == normalize_whitespace(expected)


def test_long_promise_chain(tmpdir) -> None:
    FILENAME = "long_promise.ts"
    # language=typescript
    FILE_CONTENT = """
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
            return getTable(trxOrKnex, lockTable, schemaName).select('*');
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
        .then((dataThree: any)=> {
            return fetchUserPosts(dataThree);
        })
        .catch((error) => {
            console.error('Error:', error.message);
        })
        .finally(() => {
            console.log('Cleanup operations here');
        });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_function("ensureTable")
        promise_chain = function_symbol.promise_chains[0]

        async_await_code = promise_chain.convert_to_async_await(inplace_edit=False)
        expected = """
        try {
        let exists = await getSchemaBuilder(trxOrKnex, schemaName)
        .hasTable(tableName);
            await !exists && _createMigrationTable(tableName, schemaName, trxOrKnex);
            exists = await getSchemaBuilder(trxOrKnex, schemaName).hasTable(lockTable);
            await (
            !exists && _createMigrationLockTable(lockTable, schemaName, trxOrKnex)
            );
            let data = await getTable(trxOrKnex, lockTable, schemaName).select('*');
            await (
            !data.length && _insertLockRowIfNeeded(tableName, schemaName, trxOrKnex)
            );
            await fetchUserData(1);
            let dataTwo: any = await fetchUserPosts(1);
            await fetchPostComments(dataTwo);
            let dataThree: any = await fetchWithTimeout(1, 500);
        return fetchUserPosts(dataThree);
        } catch(error: any) {
        console.error('Error:', error.message);
        } finally {
        console.log('Cleanup operations here');
        }
        """
        assert normalize_whitespace(async_await_code) == normalize_whitespace(expected)


def test_complex_returns_with_anonymous_function(tmpdir) -> None:
    FILENAME = "complex_returns.ts"
    # language=typescript
    FILE_CONTENT = """
    function create(opts: any): Promise<any> {
        let qResponse = this.request(opts);
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
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_function("create")
        promise_chain = function_symbol.promise_chains[0]

        async_await_code = promise_chain.convert_to_async_await(inplace_edit=False)
        expected = """
        let response = await qResponse;
        qResponse = await (async (response) => {
            if (response.statusCode < 200 || response.statusCode >= 300) {
                throw new Error(response);
            }
            if (typeof response.body === "string") {
                return JSON.parse(response.body);
            }
            return response.body;
        })(response);
        """
        assert normalize_whitespace(async_await_code) == normalize_whitespace(expected)


def test_file_promise_chains(tmpdir) -> None:
    FILENAME = "multiple_functions.ts"
    # language=typescript
    FILE_CONTENT = """
    function first(): Promise<number> {
        return Promise.resolve(10).then(value => value * 2);
    }

    function second(): Promise<string> {
        return fetchUserData(1)
            .then(user => user.name)
            .catch(error => 'default');
    }

    function noPromise(): number {
        return 42;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILENAME)
        promise_chains = file.promise_chains

        # Should find 2 promise chains (from first and second functions)
        assert len(promise_chains) == 2

        # Verify the chains are from the correct functions
        function_names = {chain.parent_function.name for chain in promise_chains}
        assert function_names == {"first", "second"}

        # Convert first chain and verify
        first_chain = next(chain for chain in promise_chains if chain.parent_function.name == "first")
        async_code = first_chain.convert_to_async_await(inplace_edit=False)
        expected = """
        let value = await Promise.resolve(10);
        return value * 2;
        """
        assert normalize_whitespace(async_code) == normalize_whitespace(expected)


def test_function_promise_chains_multiple(tmpdir) -> None:
    FILENAME = "multiple_chains.ts"
    # language=typescript
    FILE_CONTENT = """
    function multipleChains(): void {
        // First chain
        Promise.resolve(1)
            .then(x => x + 1)
            .catch(err => console.error(err));

        // Second chain
        fetchUserData(1)
            .then(user => user.posts)
            .then(posts => console.log(posts));
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_function("multipleChains")
        chains = function_symbol.promise_chains

        # Should find both promise chains
        assert len(chains) == 2

        # Convert first chain and verify
        first_chain_code = chains[0].convert_to_async_await(inplace_edit=False)
        expected_first = """
        try {
            let x = await Promise.resolve(1);
            await x + 1;
        } catch(err: any) {
            console.error(err);
        }
        """
        assert normalize_whitespace(first_chain_code) == normalize_whitespace(expected_first)


def test_promise_chain_attributes(tmpdir) -> None:
    FILENAME = "chain_attributes.ts"
    # language=typescript
    FILE_CONTENT = """
    function chainWithAll(): Promise<void> {
        return fetchUserData(1)
            .then(user => user.posts)
            .catch(error => {
                console.error(error);
                throw error;
            })
            .finally(() => {
                console.log('Done');
            });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_function("chainWithAll")
        chain = function_symbol.promise_chains[0]

        # Test chain attributes
        assert chain.has_catch_call
        assert chain.has_finally_call
        assert len(chain.then_chain) == 1
        assert chain.parent_function.name == "chainWithAll"
