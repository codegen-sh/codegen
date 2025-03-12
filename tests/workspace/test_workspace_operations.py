from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.workspace import Workspace


def test_view_file(tmpdir) -> None:
    # language=python
    content = """
def hello():
    print("Hello, world!")

class Greeter:
    def greet(self):
        return "Hi!"

from typing import List
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        workspace = Workspace(codebase)

        # Test viewing an existing file
        result = workspace.view_file("test.py")
        assert result["filepath"] == "test.py"
        assert "def hello():" in result["content"]
        assert result["extension"] == ".py"
        assert result["name"] == "test"
        assert "hello" in result["functions"]
        assert "Greeter" in result["classes"]
        assert "from typing import List" in result["imports"]

        # Test viewing a non-existent file
        try:
            workspace.view_file("nonexistent.py")
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError:
            pass


def test_list_directory(tmpdir) -> None:
    # language=python
    files = {
        "src/main.py": "print('main')",
        "src/utils/helper.py": "print('helper')",
        "src/utils/tools.py": "print('tools')",
    }

    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        workspace = Workspace(codebase)

        # Test listing root directory
        root_result = workspace.list_directory("./")
        assert root_result["name"] == ""  # Root directory has empty name
        assert "src" in root_result["subdirectories"]  # Just directory name
        assert len(root_result["files"]) == 0  # No files in root

        # Test listing src directory
        src_result = workspace.list_directory("src")
        assert src_result["name"] == "src"
        assert "main.py" in src_result["files"]  # Just filename
        assert "utils" in src_result["subdirectories"]  # Just directory name

        # Test listing utils directory
        utils_result = workspace.list_directory("src/utils")
        assert utils_result["name"] == "utils"
        assert "helper.py" in utils_result["files"]  # Just filename
        assert "tools.py" in utils_result["files"]  # Just filename
        assert len(utils_result["subdirectories"]) == 0  # No subdirectories

        # Test listing non-existent directory
        try:
            workspace.list_directory("nonexistent")
            assert False, "Should raise NotADirectoryError"
        except NotADirectoryError:
            pass


def test_search(tmpdir) -> None:
    # language=python
    files = {
        "src/users.py": """
def get_user(id: int):
    return {"id": id}

def create_user(name: str):
    return {"name": name}
""",
        "src/posts.py": """
def get_post(id: int):
    return {"id": id}
""",
    }

    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        workspace = Workspace(codebase)

        # Test searching across all files
        all_results = workspace.search("get_")
        assert len(all_results["results"]) == 2  # Should find in both files

        # Test searching with directory filter
        filtered_results = workspace.search("get_", target_directories=["src/users.py"])
        assert len(filtered_results["results"]) == 1  # Should only find in users.py


def test_file_operations(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir) as codebase:
        workspace = Workspace(codebase)

        # Test creating a file
        create_result = workspace.create_file("test.py", "print('hello')")
        assert create_result["filepath"] == "test.py"
        assert "print('hello')" in create_result["content"]

        # Test creating a duplicate file
        try:
            workspace.create_file("test.py")
            assert False, "Should raise FileExistsError"
        except FileExistsError:
            pass

        # Test editing a file
        edit_result = workspace.edit_file("test.py", "print('updated')")
        assert "print('updated')" in edit_result["content"]

        # Test deleting a file
        delete_result = workspace.delete_file("test.py")
        assert delete_result["status"] == "success"
        assert delete_result["deleted_file"] == "test.py"

        # Test deleting non-existent file
        try:
            workspace.delete_file("nonexistent.py")
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError:
            pass


def test_commit(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir) as codebase:
        workspace = Workspace(codebase)

        # Create and edit some files
        workspace.create_file("test.py", "print('hello')")
        workspace.edit_file("test.py", "print('updated')")

        # Test commit
        result = workspace.commit()
        assert result["status"] == "success"

        # Verify changes persisted
        view_result = workspace.view_file("test.py")
        assert "print('updated')" in view_result["content"]


def test_reveal_symbol(tmpdir) -> None:
    # language=python
    files = {
        "src/data.py": """
from src.utils import validate_input

def process_data(data: str) -> dict:
    if validate_input(data):
        return {"data": data}
    return {"error": "Invalid data"}
""",
        "src/utils.py": """
def validate_input(data: str) -> bool:
    return len(data) > 0

def unused_function():
    pass
""",
        "src/api.py": """
from src.data import process_data

def handle_request(request_data: str) -> dict:
    return process_data(request_data)

def another_handler(data: str) -> dict:
    return handle_request(data)
""",
    }

    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        workspace = Workspace(codebase)

        # Test revealing process_data function with degree=1
        result = workspace.reveal_symbol("process_data", degree=1)

        # Check basic symbol info
        assert result["symbol"]["name"] == "process_data"
        assert result["symbol"]["type"] == "Function"
        assert "process_data" in result["symbol"]["source"]

        # Check immediate dependencies (should find validate_input through import)
        deps = result["dependencies"]
        assert len(deps) == 1
        assert deps[0]["name"] == "validate_input"

        # Check immediate usages (should find handle_request)
        usages = result["usages"]
        assert len(usages) == 1
        assert usages[0]["name"] == "handle_request"

        # Test with degree=2 to see deeper relationships
        deep_result = workspace.reveal_symbol("process_data", degree=2)

        # Should now see both handle_request and another_handler
        assert len(deep_result["usages"]) == 2
        usage_names = {u["name"] for u in deep_result["usages"]}
        assert usage_names == {"handle_request", "another_handler"}

        # Test revealing a symbol with no dependencies or usages
        unused_result = workspace.reveal_symbol("unused_function")
        assert len(unused_result["dependencies"]) == 0
        assert len(unused_result["usages"]) == 0

        # Test revealing non-existent symbol
        try:
            workspace.reveal_symbol("nonexistent_function")
            assert False, "Should raise ValueError"
        except ValueError:
            pass
