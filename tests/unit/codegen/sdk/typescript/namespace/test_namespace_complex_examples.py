from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.typescript.function import TSFunction
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.namespace import TSNamespace


def test_namespace_math_operations(tmpdir) -> None:
    FILE_NAME_1 = "mathOperations.ts"
    # language=typescript
    FILE_CONTENT_1 = """
export namespace MathOperations {
    export const add = (a: number, b: number): number => a + b;
    export const subtract = (a: number, b: number): number => a - b;
    export const multiply = (a: number, b: number): number => a * b;
    export const divide = (a: number, b: number): number => {
        if (b === 0) {
            throw new Error("Division by zero is not allowed.");
        }
        return a / b;
    };
}
"""
    FILE_NAME_2 = "app.ts"
    # language=typescript
    FILE_CONTENT_2 = """
import { MathOperations } from './mathOperations';

const a = 10;
const b = 5;

console.log(`Addition: ${MathOperations.add(a, b)}`);
console.log(`Subtraction: ${MathOperations.subtract(a, b)}`);
console.log(`Multiplication: ${MathOperations.multiply(a, b)}`);
console.log(`Division: ${MathOperations.divide(a, b)}`);
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME_1: FILE_CONTENT_1, FILE_NAME_2: FILE_CONTENT_2}) as codebase:
        file = codebase.get_file(FILE_NAME_2)
        namespace: TSNamespace = codebase.get_symbol("MathOperations")
        assert namespace is not None
        assert namespace.name == "MathOperations"

        # Test namespace functions
        add_func = namespace.get_function("add")
        assert add_func is not None
        assert add_func.name == "add"
        assert isinstance(add_func, TSFunction)

        subtract_func = namespace.get_function("subtract")
        assert subtract_func is not None
        assert subtract_func.name == "subtract"

        multiply_func = namespace.get_function("multiply")
        assert multiply_func is not None
        assert multiply_func.name == "multiply"

        divide_func = namespace.get_function("divide")
        assert divide_func is not None
        assert divide_func.name == "divide"

        # Verify all functions are exported
        assert add_func.is_exported
        assert subtract_func.is_exported
        assert multiply_func.is_exported
        assert divide_func.is_exported


def test_namespace_validators(tmpdir) -> None:
    """Test namespace with interface implementation and regex validation."""
    FILE_NAME = "validators.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Validation {
        export interface StringValidator {
            isAcceptable(s: string): boolean;
        }
        const lettersRegexp = /^[A-Za-z]+$/;
        const numberRegexp = /^[0-9]+$/;
        export class LettersOnlyValidator implements StringValidator {
            isAcceptable(s: string) {
                return lettersRegexp.test(s);
            }
        }
        export class ZipCodeValidator implements StringValidator {
            isAcceptable(s: string) {
                return s.length === 5 && numberRegexp.test(s);
            }
        }
    }

    // Some samples to try
    let strings = ["Hello", "98052", "101"];
    // Validators to use
    let validators: { [s: string]: Validation.StringValidator } = {};
    validators["ZIP code"] = new Validation.ZipCodeValidator();
    validators["Letters only"] = new Validation.LettersOnlyValidator();
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace: TSNamespace = codebase.get_symbol("Validation")
        assert namespace is not None
        assert namespace.name == "Validation"

        # Test interface
        validator_interface = namespace.get_interface("StringValidator")
        assert validator_interface is not None
        assert validator_interface.name == "StringValidator"
        assert validator_interface.is_exported

        # Test validator classes
        letters_validator = namespace.get_class("LettersOnlyValidator")
        assert letters_validator is not None
        assert letters_validator.name == "LettersOnlyValidator"
        assert letters_validator.is_exported

        zip_validator = namespace.get_class("ZipCodeValidator")
        assert zip_validator is not None
        assert zip_validator.name == "ZipCodeValidator"
        assert zip_validator.is_exported

        # Test class methods
        letters_acceptable = letters_validator.get_method("isAcceptable")
        assert letters_acceptable is not None
        assert letters_acceptable.name == "isAcceptable"

        zip_acceptable = zip_validator.get_method("isAcceptable")
        assert zip_acceptable is not None
        assert zip_acceptable.name == "isAcceptable"

        # Verify non-exported items are not accessible
        assert namespace.get_symbol("lettersRegexp") is None
        assert namespace.get_symbol("numberRegexp") is None
