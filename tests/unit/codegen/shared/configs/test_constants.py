from pathlib import Path

from codegen.shared.configs.constants import (
    CODEGEN_DIR_NAME,
    CODEGEN_REPO_ROOT,
    CONFIG_FILENAME,
    CONFIG_PATH,
)


def test_codegen_repo_root_is_path():
    assert isinstance(CODEGEN_REPO_ROOT, Path)
    assert CODEGEN_REPO_ROOT.exists()
    assert CODEGEN_REPO_ROOT.is_dir()


def test_config_path_construction():
    expected_path = CODEGEN_REPO_ROOT / CODEGEN_DIR_NAME / CONFIG_FILENAME
    assert CONFIG_PATH == expected_path
    assert str(CONFIG_PATH).endswith(f"{CODEGEN_DIR_NAME}/{CONFIG_FILENAME}")
    assert CONFIG_PATH.exists()
    assert CONFIG_PATH.is_file()
