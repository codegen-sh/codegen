from pathlib import Path

from platformdirs import user_cache_dir

cachedir = Path(user_cache_dir("codegen-on-oss", "codegen"))
