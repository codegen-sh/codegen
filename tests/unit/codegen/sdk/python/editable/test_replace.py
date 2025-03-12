from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_replace_all(tmpdir) -> None:
    # language=typescript
    content = """
/**
 * Calculates the area of a rectangle.
 *
 * @param width - The width of the rectangle in units.
 * @param height - The height of the rectangle in units.
 * @returns The area of the rectangle in square units.
 *
 * @example
 * const area = calculateRectangleArea(5, 3);
 * console.log(area); // Output: 15
 */
function calculateRectangleArea(a: string, b?: string, c?: boolean): string {
    x = a + b + c
    y = b + b + a
    z = c + a + b
    return x + y + z + a
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        file.replace("a", "A")
    # language=typescript
    assert (
        file.content
        == """
/**
 * CAlculAtes the AreA of A rectAngle.
 *
 * @pArAm width - The width of the rectAngle in units.
 * @pArAm height - The height of the rectAngle in units.
 * @returns The AreA of the rectAngle in squAre units.
 *
 * @exAmple
 * const AreA = cAlculAteRectAngleAreA(5, 3);
 * console.log(AreA); // Output: 15
 */
function cAlculAteRectAngleAreA(A: string, b?: string, c?: booleAn): string {
    x = A + b + c
    y = b + b + A
    z = c + A + b
    return x + y + z + A
}
    """
    )


def test_replace_all_using_regex(tmpdir) -> None:
    # language=typescript
    content = """
/**
 * Calculates the area of a rectangle.
 *
 * @param width - The width of the rectangle in units.
 * @param height - The height of the rectangle in units.
 * @returns The area of the rectangle in square units.
 *
 * @example
 * const area = calculateRectangleArea(5, 3);
 * console.log(area); // Output: 15
 */
function calculateRectangleArea(a: string, b?: string, c?: boolean): string {
    x = a + b + c
    y = b + b + a
    z = c + a + b
    return x + y + z + a
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        file.replace(r"\ba\b", "A", is_regex=True)
    # language=typescript
    assert (
        file.content
        == """
/**
 * Calculates the area of A rectangle.
 *
 * @param width - The width of the rectangle in units.
 * @param height - The height of the rectangle in units.
 * @returns The area of the rectangle in square units.
 *
 * @example
 * const area = calculateRectangleArea(5, 3);
 * console.log(area); // Output: 15
 */
function calculateRectangleArea(A: string, b?: string, c?: boolean): string {
    x = A + b + c
    y = b + b + A
    z = c + A + b
    return x + y + z + A
}
    """
    )


def test_replace_up_to_count(tmpdir) -> None:
    # language=typescript
    content = """
/**
 * Calculates the area of a rectangle.
 *
 * @param width - The width of the rectangle in units.
 * @param height - The height of the rectangle in units.
 * @returns The area of the rectangle in square units.
 *
 * @example
 * const area = calculateRectangleArea(5, 3);
 * console.log(area); // Output: 15
 */
function calculateRectangleArea(a: string, b?: string, c?: boolean): string {
    x = a + b + c
    y = b + b + a
    z = c + a + b
    return x + y + z + a
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        file.replace("a", "A", count=32)
    # language=typescript
    assert (
        file.content
        == """
/**
 * CAlculAtes the AreA of A rectAngle.
 *
 * @pArAm width - The width of the rectAngle in units.
 * @pArAm height - The height of the rectAngle in units.
 * @returns The AreA of the rectAngle in squAre units.
 *
 * @exAmple
 * const AreA = cAlculAteRectAngleAreA(5, 3);
 * console.log(AreA); // Output: 15
 */
function cAlculAteRectAngleAreA(A: string, b?: string, c?: booleAn): string {
    x = A + b + c
    y = b + b + a
    z = c + a + b
    return x + y + z + a
}
    """
    )
