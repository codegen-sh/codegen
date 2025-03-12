from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_import_edge_case(tmpdir) -> None:
    # language=typescript
    content = """
import './module.js'

// Generic mock function with configurable return value
const mockRequire = (returnValue = 'result') => returnValue

// Generic path constants with configurable values
const MOCK_DIR_PATH = 'mock/directory/path'
const MOCK_FILE_PATH = 'mock/directory/path/file.js'

it('should support CommonJS globals in ESM context', () => {
  const require = mockRequire
  const __dirname = MOCK_DIR_PATH
  const __filename = MOCK_FILE_PATH

  expect(require()).toBe('result')
  expect(__dirname).toBe(MOCK_DIR_PATH)
  expect(__filename).toBe(MOCK_FILE_PATH)
})    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        assert len(file.imports) == 1
