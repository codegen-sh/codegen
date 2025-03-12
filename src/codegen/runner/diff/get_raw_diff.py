import io

from unidiff import LINE_TYPE_CONTEXT, Hunk, PatchedFile, PatchSet
from unidiff.patch import Line

from codegen.sdk.core.codebase import Codebase
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def append_flag(file: PatchedFile, append_at: int, line_no: int, codebase: Codebase) -> None:
    added_hunk = Hunk(
        src_start=line_no,
        src_len=1,
        tgt_start=line_no,
        tgt_len=1,
    )
    line = codebase.get_file(file.path).content.split("\n")[line_no - 1]
    added_hunk.append(Line(f"{line}\n", line_type=LINE_TYPE_CONTEXT))
    file.insert(append_at, added_hunk)


def patch_to_limited_diff_string(patch, codebase: Codebase, max_lines=10000):
    diff_lines = []
    total_lines = 0

    # Add flags that are not in the diff
    filenames = [patched_file.path for patched_file in patch]
    flags_not_in_diff = list(filter(lambda flag: flag.symbol.filepath not in filenames, codebase.ctx.flags._flags))

    for flag in flags_not_in_diff:
        filename = flag.symbol.filepath
        patched_file = PatchedFile(
            patch_info=f"diff --git a/{filename} b/{filename}\n",
            source=f"a/{filename}",
            target=f"b/{filename}",
        )
        patch.append(patched_file)

    for patched_file in patch:
        filtered_flags = filter(lambda flag: flag.symbol.filepath == patched_file.path, codebase.ctx.flags._flags)
        sorted_flags = list(map(lambda flag: flag.symbol.start_point.row + 1, filtered_flags))
        sorted_flags.sort()

        for flag in sorted_flags:
            is_in_diff = False

            for i, hunk in enumerate(patched_file):
                contains_flag = hunk.source_start <= flag <= hunk.source_start + hunk.source_length

                if contains_flag:
                    is_in_diff = True
                    break

                is_after_flag = hunk.source_start > flag

                if is_after_flag:
                    is_in_diff = True
                    append_flag(patched_file, i, flag, codebase)
                    break

            if not is_in_diff:
                append_flag(patched_file, len(patched_file), flag, codebase)

        # Add file header
        raw_diff = str(patched_file)
        diff_length = len(raw_diff.splitlines())

        total_lines += diff_length
        diff_lines.append(raw_diff)

        if total_lines >= max_lines:
            break

    return "\n".join(diff_lines)


def get_raw_diff(codebase: Codebase, base: str = "HEAD", max_lines: int = 10000) -> str:
    raw_diff = codebase.get_diff(base)
    patch_set = PatchSet(io.StringIO(raw_diff))

    raw_diff_length = len(raw_diff.split("\n"))
    logger.info(f"Truncating diff (total: {raw_diff_length}) to {max_lines} lines ...")
    raw_diff_trunc = patch_to_limited_diff_string(patch=patch_set, max_lines=max_lines, codebase=codebase)

    return raw_diff_trunc


def get_filenames_from_diff(diff: str) -> list[str]:
    patch_set = PatchSet(io.StringIO(diff))
    filenames = [patched_file.path for patched_file in patch_set]

    return filenames
