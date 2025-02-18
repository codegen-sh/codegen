from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_binary_expressions(tmpdir):
    # language=typescript
    content = """
let a: number = 1 + 2;
let b: number = 3 - 4;
let c: number = 5 * 6;
let d: number = 7 / 8;
let e: number = 9 % 10;
let f: number = 11 ** 12;
let g: number = 13 ?? 14;
let h: number = 15 & 16;
let i: number = 17 | 18;
let j: number = 19 ^ 20;
let k: number = 21 << 22;
let l: number = 23 >> 24;
let m: boolean = 25 === 26;
let n: boolean = 27 !== 28;
let o: boolean = 29 > 30;
let p: boolean = 31 < 32;
let q: boolean = 33 >= 34;
let r: boolean = 35 <= 36;
let s: boolean = 37 && 38;
let t: boolean = 39 || 40;
let u: boolean = 41 instanceof 42;
let v: boolean = 43 in 44;
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        assert all([isinstance(var.value, BinaryExpression) for var in file.global_vars])

        assert file.get_global_var("a").value.left.source == "1"
        assert file.get_global_var("a").value.right.source == "2"
        assert file.get_global_var("a").value.operator.source == "+"

        assert file.get_global_var("b").value.left.source == "3"
        assert file.get_global_var("b").value.right.source == "4"
        assert file.get_global_var("b").value.operator.source == "-"

        assert file.get_global_var("c").value.left.source == "5"
        assert file.get_global_var("c").value.right.source == "6"
        assert file.get_global_var("c").value.operator.source == "*"

        assert file.get_global_var("d").value.left.source == "7"
        assert file.get_global_var("d").value.right.source == "8"
        assert file.get_global_var("d").value.operator.source == "/"

        assert file.get_global_var("e").value.left.source == "9"
        assert file.get_global_var("e").value.right.source == "10"
        assert file.get_global_var("e").value.operator.source == "%"

        assert file.get_global_var("f").value.left.source == "11"
        assert file.get_global_var("f").value.right.source == "12"
        assert file.get_global_var("f").value.operator.source == "**"

        assert file.get_global_var("g").value.left.source == "13"
        assert file.get_global_var("g").value.right.source == "14"
        assert file.get_global_var("g").value.operator.source == "??"

        assert file.get_global_var("h").value.left.source == "15"
        assert file.get_global_var("h").value.right.source == "16"
        assert file.get_global_var("h").value.operator.source == "&"

        assert file.get_global_var("i").value.left.source == "17"
        assert file.get_global_var("i").value.right.source == "18"
        assert file.get_global_var("i").value.operator.source == "|"

        assert file.get_global_var("j").value.left.source == "19"
        assert file.get_global_var("j").value.right.source == "20"
        assert file.get_global_var("j").value.operator.source == "^"

        assert file.get_global_var("k").value.left.source == "21"
        assert file.get_global_var("k").value.right.source == "22"
        assert file.get_global_var("k").value.operator.source == "<<"

        assert file.get_global_var("l").value.left.source == "23"
        assert file.get_global_var("l").value.right.source == "24"
        assert file.get_global_var("l").value.operator.source == ">>"

        assert file.get_global_var("m").value.left.source == "25"
        assert file.get_global_var("m").value.right.source == "26"
        assert file.get_global_var("m").value.operator.source == "==="

        assert file.get_global_var("n").value.left.source == "27"
        assert file.get_global_var("n").value.right.source == "28"
        assert file.get_global_var("n").value.operator.source == "!=="

        assert file.get_global_var("o").value.left.source == "29"
        assert file.get_global_var("o").value.right.source == "30"
        assert file.get_global_var("o").value.operator.source == ">"

        assert file.get_global_var("p").value.left.source == "31"
        assert file.get_global_var("p").value.right.source == "32"
        assert file.get_global_var("p").value.operator.source == "<"

        assert file.get_global_var("q").value.left.source == "33"
        assert file.get_global_var("q").value.right.source == "34"
        assert file.get_global_var("q").value.operator.source == ">="

        assert file.get_global_var("r").value.left.source == "35"
        assert file.get_global_var("r").value.right.source == "36"
        assert file.get_global_var("r").value.operator.source == "<="

        assert file.get_global_var("s").value.left.source == "37"
        assert file.get_global_var("s").value.right.source == "38"
        assert file.get_global_var("s").value.operator.source == "&&"

        assert file.get_global_var("t").value.left.source == "39"
        assert file.get_global_var("t").value.right.source == "40"
        assert file.get_global_var("t").value.operator.source == "||"

        assert file.get_global_var("u").value.left.source == "41"
        assert file.get_global_var("u").value.right.source == "42"
        assert file.get_global_var("u").value.operator.source == "instanceof"

        assert file.get_global_var("v").value.left.source == "43"
        assert file.get_global_var("v").value.right.source == "44"
        assert file.get_global_var("v").value.operator.source == "in"


def test_chained_binary_expressions(tmpdir):
    # language=typescript
    content = """
// binary operators
let a: number = 1 + 2 - 3 * 4 / 5 % 6 ** 7 | 0;

// comparison operators
let b: boolean = 9 == 10 && 10 != 11 && 11 < 12 && 12 > 13 && 13 <= 14

// boolean operators
let c: boolean = true && false || false && true || false;
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")

        a = file.get_global_var("a").value
        assert [x.source for x in a.elements] == ["1", "2", "3", "4", "5", "6", "7", "0"]
        assert [x.source for x in a.operators] == ["+", "-", "*", "/", "%", "**", "|"]

        b = file.get_global_var("b").value
        assert [x.source for x in b.elements] == ["9", "10", "10", "11", "11", "12", "12", "13", "13", "14"]
        assert [x.source for x in b.operators] == ["==", "&&", "!=", "&&", "<", "&&", ">", "&&", "<="]

        c = file.get_global_var("c").value
        assert [x.source for x in c.elements] == ["true", "false", "false", "true", "false"]
        assert [x.source for x in c.operators] == ["&&", "||", "&&", "||"]
