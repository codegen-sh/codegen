from typing import TYPE_CHECKING

from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import CodebaseType, PyCodebaseType, TSCodebaseType
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol_groups.dict import Dict
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCaseTSFile

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.core.type_alias import TypeAlias

ts_input1 = """
export type MyMapper<K,V> = {
	convert: (
		value: Table[K],
	) => Record[V]

	getFromMethod: (
		value: Table[K],
	) => Array<Record[V]>

	toTable: (table: V) => K
}
"""
ts_input2 = """
import { MyMapper } from './mappers';

export const mapperImpl: MyMapper<K1,V1> = {
    convert(value: Table[K1]): Record[V1] {
        return Record[V1](value);
    },

    getFromMethod(value: Table[K]): Array<Record[V]> {
        return [Record[V](value)];
    },

    toTable(table: V1): K1 {
        return K1(table);
    }
}
"""
ts_input3 = """
import { MyMapper } from './mappers';

export function createMapper<K2, V2>(): MyMapper<K2, V2> {
	const mapper = {
        convert: (
            value: Table[K2],
        ): Record[V2] => {
            return mapper.getOnlyValueFromPostgres(value)
        },

        getFromMethod(value: Table[K2]
            ): Array<Record[V2]> => {
            return [Record[V2](value)];
        },

        toTable(table: V2): K2 => {
            return K2(table);
        }
	}
	return mapper
}
"""
ts_input4 = """
import { MyMapper } from './mappers';

export class MapperClass<K3, V3> implements MyMapper<K3, V3> {
    convert(value: Table[K3]): Record[V3] {
        return Record[V3](value);
    }
    getFromMethod(value: Table[K3]): Array<Record[V3]> {
        return [Record[V3](value)];
    }
    toTable(table: V3): K3 {
        return K3(table);
    }
}
"""
ts_input5 = """
import { MyMapper } from './mappers';
import { mapperImpl } from './file1';
import { createMapper } from './file2';
import { MapperClass } from './file3';

var myMapper: MyMapper<K,V> = createMapper();

function main() {
    const var1 = mapperImpl.convert(1);
    const var2 = mapperImpl.getFromMethod(2);
    const var3 = mapperImpl.toTable(3);

    const var4 = myMapper.convert(4);
    const var5 = myMapper.getFromMethod(5);
    const var6 = myMapper.toTable(6);

    const var7 = MapperClass.convert(7);
    const var8 = MapperClass.getFromMethod(8);
    const var9 = MapperClass.toTable(9);
}
"""


ts_output1 = """
export type MyMapper<K,V> = {
	convert: (
		value: Table[K],
	) => Promise<Record[V]>

	getFromMethod: (
		value: Table[K],
	) => Array<Record[V]>

	toTable: (table: V) => K
}
"""
ts_output2 = """
import { MyMapper } from './mappers';

export const mapperImpl: MyMapper<K1,V1> = {
    async convert(value: Table[K1]): Promise<Record[V1]> {
        return Record[V1](value);
    },

    getFromMethod(value: Table[K]): Array<Record[V]> {
        return [Record[V](value)];
    },

    toTable(table: V1): K1 {
        return K1(table);
    }
}
"""
ts_output3 = """
import { MyMapper } from './mappers';

export function createMapper<K2, V2>(): MyMapper<K2, V2> {
	const mapper = {
        convert: async (
            value: Table[K2],
        ): Promise<Record[V2]> => {
            return mapper.getOnlyValueFromPostgres(value)
        },

        getFromMethod(value: Table[K2]
            ): Array<Record[V2]> => {
            return [Record[V2](value)];
        },

        toTable(table: V2): K2 => {
            return K2(table);
        }
	}
	return mapper
}
"""
ts_output4 = """
import { MyMapper } from './mappers';

export class MapperClass<K3, V3> implements MyMapper<K3, V3> {
    async convert(value: Table[K3]): Promise<Record[V3]> {
        return Record[V3](value);
    }
    getFromMethod(value: Table[K3]): Array<Record[V3]> {
        return [Record[V3](value)];
    }
    toTable(table: V3): K3 {
        return K3(table);
    }
}
"""
ts_output5 = """
import { MyMapper } from './mappers';
import { mapperImpl } from './file1';
import { createMapper } from './file2';
import { MapperClass } from './file3';

var myMapper: MyMapper<K,V> = createMapper();

async function main() {
    const var1 = await (mapperImpl.convert(1));
    const var2 = mapperImpl.getFromMethod(2);
    const var3 = mapperImpl.toTable(3);

    const var4 = await (myMapper.convert(4));
    const var5 = myMapper.getFromMethod(5);
    const var6 = myMapper.toTable(6);

    const var7 = await (MapperClass.convert(7));
    const var8 = MapperClass.getFromMethod(8);
    const var9 = MapperClass.toTable(9);
}
"""
ts_files_readonly = [
    SkillTestCaseTSFile(input=ts_input1, output=ts_input1, filepath="mappers.ts"),
    SkillTestCaseTSFile(input=ts_input2, output=ts_input2, filepath="file1.ts"),
    SkillTestCaseTSFile(input=ts_input3, output=ts_input3, filepath="file2.ts"),
    SkillTestCaseTSFile(input=ts_input4, output=ts_input4, filepath="file3.ts"),
    SkillTestCaseTSFile(input=ts_input5, output=ts_input5, filepath="file4.ts"),
]

ts_files_write = [
    SkillTestCaseTSFile(input=ts_input1, output=ts_output1, filepath="mappers.ts"),
    SkillTestCaseTSFile(input=ts_input2, output=ts_output2, filepath="file1.ts"),
    SkillTestCaseTSFile(input=ts_input3, output=ts_output3, filepath="file2.ts"),
    SkillTestCaseTSFile(input=ts_input4, output=ts_output4, filepath="file3.ts"),
    SkillTestCaseTSFile(input=ts_input5, output=ts_output5, filepath="file4.ts"),
]


@skill(eval_skill=False, prompt="Gets all set of symbols that can inherits, extends, or implements a given type symbol.", uid="8b2442b5-aa5e-44c5-bebc-640f7cf7f2d7")
class SearchTypeAliasInheritanceSkill(Skill):
    """Gets all implementation instances of type alias 'MyMapper' in TypeScript codebase."""

    @staticmethod
    def python_skill_func(codebase: PyCodebaseType) -> callable:
        pass

    @staticmethod
    def skill_func(codebase: CodebaseType):
        pass

    @staticmethod
    @skill_impl([SkillTestCase(files=ts_files_readonly)], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        """Given a type alias 'MyMapper', find all inherited or extended implementations of the type object.
        Loops through all codebase symbols and handles each symbol type accordingly.
        """
        mapper_symbol: TypeAlias = codebase.get_symbol("MyMapper")
        mapper_dict: Dict = mapper_symbol.value

        # Collect all implementations of the mapper type
        mapper_impl: list[tuple[Symbol, MutableMapping]] = []

        for symbol in codebase.symbols:
            if isinstance(symbol, Assignment):
                # Check if the global variable initializes a mapper implementation
                if symbol.type and symbol.type.name == "MyMapper" and isinstance(symbol.value, Dict):
                    mapper_impl.append((symbol, symbol.value))
            elif isinstance(symbol, Function):
                if symbol.return_type and symbol.return_type.name == "MyMapper":
                    # Search for the assignment statement that implements the mapper type
                    for statement in symbol.code_block.assignment_statements:
                        if (val := statement.right) and isinstance(val, Dict) and set(val.keys()) == set(mapper_dict.keys()):
                            mapper_impl.append((symbol, val))
                            break
            elif isinstance(symbol, Class):
                if mapper_symbol in symbol.superclasses:
                    mapper_impl.append((symbol, {**{x.name: x for x in symbol.methods}}))

        assert len(mapper_impl) == 3
        assert all([set(val.keys()) == set(mapper_dict.keys()) for _, val in mapper_impl])


@skill(eval_skill=False, prompt="Converts a specified set of functions in an object type to be asynchronous.", uid="d091ab15-0071-407b-bf1a-e89aeb69add9")
class AsyncifyTypeAliasElements(Skill):
    """Given a type alias 'MyMapper' containing synchronous methods, convert 'getFromMethod' method to be asynchronous.
    The inherited implementations of the type alias as well as all their call sites are also update.
    """

    @staticmethod
    def python_skill_func(codebase: PyCodebaseType) -> callable:
        pass

    @staticmethod
    def skill_func(codebase: CodebaseType):
        pass

    @staticmethod
    @skill_impl([SkillTestCase(files=ts_files_write)], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        FUNC_NAME_TO_CONVERT = "convert"

        mapper_symbol: TypeAlias = codebase.get_symbol("MyMapper")
        mapper_dict: Dict = mapper_symbol.value
        # Update the base type alias definition
        mapper_dict[FUNC_NAME_TO_CONVERT].asyncify()

        # Collect all implementations of the mapper type
        mapper_impl: list[tuple[Symbol, MutableMapping]] = []

        for symbol in codebase.symbols:
            if isinstance(symbol, Assignment):
                # Check if the global variable initializes a mapper implementation
                if symbol.type and symbol.type.name == "MyMapper" and isinstance(symbol.value, Dict):
                    mapper_impl.append((symbol, symbol.value))
            elif isinstance(symbol, Function):
                if symbol.return_type and symbol.return_type.name == "MyMapper":
                    # Search for the assignment statement that implements the mapper type
                    for statement in symbol.code_block.assignment_statements:
                        if (val := statement.right) and isinstance(val, Dict) and set(val.keys()) == set(mapper_dict.keys()):
                            mapper_impl.append((symbol, val))
                            break
            elif isinstance(symbol, Class):
                if mapper_symbol in symbol.superclasses:
                    mapper_impl.append((symbol, {**{x.name: x for x in symbol.methods}}))

        # Update the mapper type alias implementations
        usages_to_check = []
        for symbol, val in mapper_impl:
            func_to_convert = val[FUNC_NAME_TO_CONVERT]
            if not func_to_convert.is_async:
                func_to_convert.asyncify()
            # Collect usages of the type alias implementations
            usages_to_check.extend(symbol.symbol_usages)

        files_to_check = set(u.file for u in usages_to_check)
        funcs_to_asyncify = []
        for file in files_to_check:
            for f_call in file.function_calls:
                if FUNC_NAME_TO_CONVERT in f_call.name:
                    if not f_call.is_awaited:
                        f_call.edit(f"await ({f_call.source})")
                    if parent_func := f_call.parent_function:
                        funcs_to_asyncify.append(parent_func)

        # Asyncify all functions that are called by the async functions
        processed = set()
        while funcs_to_asyncify:
            f = funcs_to_asyncify.pop()
            if f in processed:
                continue

            processed.add(f)
            if not f.is_async:
                f.asyncify()

                for call_site in f.call_sites:
                    if call_site.parent and isinstance(call_site.parent, Function):
                        funcs_to_asyncify.append(call_site.parent)
