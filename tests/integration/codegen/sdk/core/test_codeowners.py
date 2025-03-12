import pytest
from codeowners import CodeOwners


@pytest.fixture
def example_codeowners_file_contents() -> str:
    return """# CODEOWNERS file example

/src/codemods   @user-a
/src/codegen    @org/team1
"""


def test_codebase_codeowners(codebase, example_codeowners_file_contents):
    codebase.ctx.codeowners_parser = CodeOwners(example_codeowners_file_contents)

    assert isinstance(codebase.codeowners, list)
    assert len(codebase.codeowners) == 2
    codeowners_by_name = {codeowner.name: codeowner for codeowner in codebase.codeowners}
    assert codeowners_by_name["@user-a"].owner_type == "USERNAME"
    assert codeowners_by_name["@org/team1"].owner_type == "TEAM"

    for _file in codeowners_by_name["@org/team1"]:
        assert _file.filepath.startswith("src/codegen")

    for _file in codeowners_by_name["@user-a"]:
        assert _file.filepath.startswith("src/codemods")
