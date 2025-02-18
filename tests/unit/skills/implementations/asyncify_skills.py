from collections import deque

from codegen.sdk.core.codebase import CodebaseType, PyCodebaseType, TSCodebaseType
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

py_input1 = """
def func_to_convert(a: int) -> int:
    return a + 1

def func_usage(a: int) -> int:
    return func_to_convert(a) + 1

class MyClass:
    def method_1(self, a: int) -> int:
        print("hello")
        return func_usage(a) + 1

    def method_2(self, b: int) -> int:
        print("world")
        return func_to_convert(b) + 1
"""
py_input2 = """
from file1 import func_to_convert, func_usage, MyClass

def main():
    my_instance = MyClass()
    print(my_instance.method_1(1))
    print(func_to_convert(1) + func_usage(2))
"""
py_output1 = """
async def func_to_convert(a: int) -> int:
    return a + 1

async def func_usage(a: int) -> int:
    return await (func_to_convert(a)) + 1

class MyClass:
    async def method_1(self, a: int) -> int:
        print("hello")
        return await (func_usage(a)) + 1

    async def method_2(self, b: int) -> int:
        print("world")
        return await (func_to_convert(b)) + 1
"""
py_output2 = """
from file1 import func_to_convert, func_usage, MyClass

async def main():
    my_instance = MyClass()
    print(await my_instance.method_1(1))
    print(await (func_to_convert(1)) + await (func_usage(2)))
"""
py_files = [
    SkillTestCasePyFile(input=py_input1, output=py_output1, filepath="file1.py"),
    SkillTestCasePyFile(input=py_input2, output=py_output2, filepath="file2.py"),
]

ts_input1 = """
export function funcToConvert(a: number): number {
    return a + 1;
}

export function funcUsage(a: number): number {
    return funcToConvert(a) + 1;
}

export class MyClass {
    method1(a: number): number {
        console.log("hello");
        return funcUsage(a) + 1;
    }

    method2(b: number): number {
        console.log("world");
        return funcToConvert(b) + 1;
    }
}
"""
ts_input2 = """
import { funcToConvert, funcUsage, MyClass } from './file1';

function main(): void {
    const myInstance = new MyClass();
    console.log(myInstance.method1(1));
    console.log(funcToConvert(1) + funcUsage(2));
}
"""
ts_output1 = """
export async function funcToConvert(a: number): Promise<number> {
    return a + 1;
}

export async function funcUsage(a: number): Promise<number> {
    return await (funcToConvert(a)) + 1;
}

export class MyClass {
    async method1(a: number): Promise<number> {
        console.log("hello");
        return await (funcUsage(a)) + 1;
    }

    async method2(b: number): Promise<number> {
        console.log("world");
        return await (funcToConvert(b)) + 1;
    }
}
"""
ts_output2 = """
import { funcToConvert, funcUsage, MyClass } from './file1';

async function main(): Promise<void> {
    const myInstance = new MyClass();
    console.log(await (myInstance.method1(1)));
    console.log(await (funcToConvert(1)) + await (funcUsage(2)));
}
"""
ts_files = [
    SkillTestCaseTSFile(input=ts_input1, output=ts_output1, filepath="file1.ts"),
    SkillTestCaseTSFile(input=ts_input2, output=ts_output2, filepath="file2.ts"),
]


@skill(eval_skill=False, prompt="Converts a signature of a synchronous function to asynchronous function", uid="2a5ba602-59e8-47d6-98ce-6dce73065c48")
class AsyncifyFunctionSkill(Skill):
    """Given a synchronous function 'func_to_convert', convert its signature to be asynchronous.
    The function's call sites as well as the call sites' functions are recursively converted as well.
    """

    @staticmethod
    def skill_func(codebase: CodebaseType):
        pass

    @staticmethod
    @skill_impl([SkillTestCase(files=py_files)], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: PyCodebaseType) -> callable:
        func_to_convert = codebase.get_function("func_to_convert")

        convert_queue = deque([func_to_convert])
        converted = set()
        while convert_queue:
            func = convert_queue.popleft()
            if func in converted:
                continue

            func.asyncify()
            converted.add(func)
            for usage in func.usages:
                if isinstance(usage.match, FunctionCall):
                    usage.match.asyncify()
                    parent_function = usage.usage_symbol
                    convert_queue.append(parent_function)

    @staticmethod
    @skill_impl([SkillTestCase(files=ts_files)], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        func_to_convert = codebase.get_function("funcToConvert")

        convert_queue = deque([func_to_convert])
        converted = set()
        while convert_queue:
            func = convert_queue.popleft()
            if func in converted:
                continue

            func.asyncify()
            converted.add(func)
            for usage in func.usages:
                if isinstance(usage.match, FunctionCall):
                    usage.match.asyncify()
                    parent_function = usage.usage_symbol
                    convert_queue.append(parent_function)
