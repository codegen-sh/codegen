from pathlib import Path

CODEGEN_DIR_NAME = ".codegen"
CONFIG_FILENAME = "config.toml"

# ====[ Codegen internal config ]====
CODEGEN_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
CODEGEN_DIR_PATH = CODEGEN_REPO_ROOT / CODEGEN_DIR_NAME
CONFIG_PATH = CODEGEN_DIR_PATH / CONFIG_FILENAME

# ====[ User session config ]====
PROMPTS_DIR = Path(CODEGEN_DIR_NAME) / "prompts"
DOCS_DIR = Path(CODEGEN_DIR_NAME) / "docs"
EXAMPLES_DIR = Path(CODEGEN_DIR_NAME) / "examples"


# ====[ User global config paths ]====
GLOBAL_CONFIG_DIR = Path("~/.config/codegen-sh").expanduser()
AUTH_FILE = GLOBAL_CONFIG_DIR / "auth.json"
SESSION_FILE = GLOBAL_CONFIG_DIR / "session.json"
GLOBAL_CONFIG_PATH = GLOBAL_CONFIG_DIR / CONFIG_FILENAME
