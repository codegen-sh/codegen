from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.class_definition import Class
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_import_rename_usage_with_alias(tmpdir) -> None:
    # language=typescript
    content1 = """
import { foo1, foo2 } from './file1';
import { bar1, bar2 } from './file2';
import * as fs from 'fs';
import * as process from 'process';

class MyClass {
    value: any;

    constructor(value: any) {
        this.value = value;
    }

    displayValue(): void {
        console.log(`Value: ${this.value}`);
    }

    calculateSum(a: number, b: number): number {
        const result: number = a + b;
        console.log(`Sum: ${result}`);
        return result;
    }

    fileOperations(filename: string): void {
        try {
            const data = fs.readFileSync(filename, 'utf-8');
            console.log(`File contents: ${data}`);
        } catch (e) {
            if (e.code === 'ENOENT') {
                console.log(`Error: File not found`);
            } else {
                throw e;
            }
        }
    }
}

function foo(): number {
    let a: number = 1;
    let b: number = 2;

    // Function call to foo1
    foo1();
    // Function call to bar1
    bar1();

    // String and array operations
    const stringSample: string = "Hello, World!";
    const listSample: number[] = [1, 2, 3, 4, 5];
    // Join operation on array
    const joinedString: string = listSample.join(', ');

    // Print joined string
    console.log(joinedString);

    // Using process to get current working directory
    const cwd: string = process.cwd();
    console.log(`Current directory: ${cwd}`);

    // Using process to get Node.js version
    const nodeVersion: string = process.version;
    console.log(`Node.js version: ${nodeVersion}`);

    // Simulating function call on integer type, will cause an error
    try {
        (a as any)(); // Casting a to any to simulate runtime error
    } catch (e) {
        if (e instanceof TypeError) {
            console.log(`Error: ${e.message}`);
        }
    }

    return b;
}

// Create an instance of MyClass and use its methods
const myInstance = new MyClass(10);
myInstance.displayValue();
myInstance.calculateSum(5, 7);
myInstance.fileOperations('example.txt');
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        for imp in codebase.imports:
            codebase.log(imp)
        for symbol in codebase.symbols:
            codebase.log(symbol)
            if hasattr(symbol, "code_block"):
                for statement in symbol.code_block.statements:
                    codebase.log(statement)
            if isinstance(symbol, Class):
                for method in symbol.methods:
                    codebase.log(method)
                    for statement in method.code_block.statements:
                        codebase.log(statement)
        for file in codebase.files:
            codebase.log(file)
            for statement in file.code_block.statements:
                codebase.log(statement)
