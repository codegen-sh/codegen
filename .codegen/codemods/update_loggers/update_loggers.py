import codegen
from codegen.sdk.core.codebase import PyCodebaseType


@codegen.function("update-loggers")
def run(codebase: PyCodebaseType) -> None:
    """Updates all loggers in src/codegen to use the new get_logger function."""
    for file in codebase.files:
        if not str(file.filepath).startswith("src/codegen/"):
            continue

        if file.get_import("logging") is None:
            continue

        if (logger := file.get_global_var("logger")) and logger.value.source == "logging.getLogger(__name__)":
            print(f"Updating logger in {file.filepath}")
            logger.set_value("get_logger(__name__)")
            file.add_import_from_import_string("\nfrom codegen.shared.logging.get_logger import get_logger")
