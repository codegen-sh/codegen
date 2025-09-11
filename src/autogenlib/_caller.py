"""Caller context extraction for autogenlib."""

import inspect
import os
import sys
from pathlib import Path
import traceback
from logging import getLogger

logger = getLogger(__name__)


def get_caller_info(max_depth=10):
    """
    Get information about the calling code.

    Args:
        max_depth: Maximum number of frames to check in the stack.

    Returns:
        dict: Information about the caller including filename and code.
    """
    try:
        # Get the current stack frames
        stack = inspect.stack()

        # Debug stack information
        logger.debug(f"Stack depth: {len(stack)}")
        for i, frame_info in enumerate(stack[:max_depth]):
            frame = frame_info.frame
            filename = frame_info.filename
            lineno = frame_info.lineno
            function = frame_info.function
            logger.debug(f"Frame {i}: {filename}:{lineno} in {function}")

        # Find the first frame that's not from autogenlib and is a real file
        caller_frame = None
        caller_filename = None

        for i, frame_info in enumerate(
            stack[1:max_depth]
        ):  # Skip the first frame (our function)
            filename = frame_info.filename

            # Skip if it's internal to Python
            if filename.startswith("<") or not os.path.exists(filename):
                continue

            # Skip if it's within our package
            if "autogenlib" in filename and "_caller.py" not in filename:
                continue

            # We found a suitable caller
            caller_frame = frame_info.frame
            caller_filename = filename
            logger.debug(f"Found caller at frame {i + 1}: {filename}")
            break

        if not caller_filename:
            # Try a different approach - look for an importing file
            for i, frame_info in enumerate(stack[1:max_depth]):
                filename = frame_info.filename

                # Skip non-file frames
                if filename.startswith("<") or not os.path.exists(filename):
                    continue

                # Check if this frame is doing an import
                if (
                    frame_info.function == "<module>"
                    or "import" in frame_info.code_context[0].lower()
                ):
                    caller_frame = frame_info.frame
                    caller_filename = filename
                    logger.debug(f"Found importing caller at frame {i + 1}: {filename}")
                    break

        # If we still didn't find a caller, use a simpler approach
        if not caller_filename:
            # Just use the top-level script
            for frame_info in reversed(stack[:max_depth]):
                filename = frame_info.filename
                if os.path.exists(filename) and not filename.startswith("<"):
                    caller_filename = filename
                    logger.debug(f"Using top-level script as caller: {filename}")
                    break

        if not caller_filename:
            logger.debug("No suitable caller file found")
            return {"code": "", "filename": ""}

        # Read the file content
        try:
            with open(caller_filename, "r") as f:
                code = f.read()

            # Get the relative path to make logs cleaner
            try:
                rel_path = Path(caller_filename).relative_to(Path.cwd())
                display_filename = str(rel_path)
            except ValueError:
                display_filename = caller_filename

            # Limit code size if it's too large to avoid excessive prompt size
            MAX_CODE_SIZE = 8000  # Characters
            if len(code) > MAX_CODE_SIZE:
                logger.debug(
                    f"Truncating large caller file ({len(code)} chars) to {MAX_CODE_SIZE} chars"
                )
                # Try to find a good place to cut (newline)
                cut_point = code[:MAX_CODE_SIZE].rfind("\n")
                if cut_point == -1:
                    cut_point = MAX_CODE_SIZE
                code = code[:cut_point] + "\n\n# ... [file truncated due to size] ..."

            logger.debug(
                f"Successfully extracted caller code from {display_filename} ({len(code)} chars)"
            )

            return {"code": code, "filename": display_filename}
        except Exception as e:
            logger.debug(f"Error reading caller file {caller_filename}: {e}")
            return {"code": "", "filename": caller_filename}
    except Exception as e:
        logger.debug(f"Error getting caller info: {e}")
        logger.debug(traceback.format_exc())
        return {"code": "", "filename": ""}
