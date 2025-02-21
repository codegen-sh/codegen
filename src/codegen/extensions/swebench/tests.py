#!/usr/bin/env python

# A no-op patch which creates an empty file is used to stand in for
# the `model_patch` and/or `test_patch` when running SWE Bench tests
# without one or both of those patches.
NOOP_PATCH = "diff --git a/empty.file.{nonce}.ignore b/empty.file.{nonce}.ignore\nnew file mode 100644\nindex 0000000..e69de29\n"


def remove_patches_to_tests(model_patch):
    """Remove any changes to the tests directory from the provided patch.
    This is to ensure that the model_patch does not disturb the repo's
    tests when doing acceptance testing with the `test_patch`.
    """
    if not model_patch:
        return model_patch

    lines = model_patch.splitlines(keepends=True)
    filtered_lines = []
    is_tests = False

    for line in lines:
        if line.startswith("diff --git a/"):
            pieces = line.split()
            to = pieces[-1]
            if to.startswith("b/") and ("/test/" in to or "/tests/" in to or "/testing/" in to or "/test_" in to or "/tox.ini" in to):
                is_tests = True
            else:
                is_tests = False

        if not is_tests:
            filtered_lines.append(line)

    return "".join(filtered_lines)
