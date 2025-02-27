from types import FrameType, TracebackType

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def get_offset_traceback(tb_lines: list[str], line_offset: int = 0, filenameFilter: str = "<string>") -> str:
    """Generate a traceback string with offset line numbers.

    :param tb_lines: lines output for the traceback
    :param line_offset: Number of lines to offset the traceback
    :return: A string containing the offset traceback
    """
    # Process each line of the traceback
    offset_tb_lines = []
    for line in tb_lines:
        if line.lstrip().startswith("File"):
            if line.lstrip().startswith(f'File "{filenameFilter}"') and "execute" not in line:
                # This line contains file and line number information
                parts = line.split(", line ")
                if len(parts) > 1:
                    # Offset the line number
                    line_num = int(parts[1].split(",")[0])
                    new_line_num = line_num - line_offset
                    line = f"{parts[0]}, line {new_line_num}{','.join(parts[1].split(',')[1:])}"
                offset_tb_lines.append(line)
        else:
            offset_tb_lines.append(line)

    # Join the processed lines back into a single string
    return "".join(offset_tb_lines)


def get_local_frame(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType) -> FrameType | None:
    LOCAL_FILENAME = "<string>"
    LOCAL_MODULE_DIR = "codegen-backend/app/"
    tb = exc_traceback
    while tb and ((tb.tb_next and tb.tb_frame.f_code.co_filename != LOCAL_FILENAME) or LOCAL_MODULE_DIR in tb.tb_frame.f_code.co_filename):
        tb = tb.tb_next

    frame = tb.tb_frame if tb else None
    return frame


def get_local_frame_context(frame: FrameType):
    local_vars = {k: v for k, v in frame.f_locals.items() if not k.startswith("__")}
    if "print" in local_vars:
        del local_vars["print"]
    if "codebase" in local_vars:
        del local_vars["codebase"]
    if "pr_options" in local_vars:
        del local_vars["pr_options"]
    return local_vars
