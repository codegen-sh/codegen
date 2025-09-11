########################################################################################################################
# MISC
########################################################################################################################


def filepath_to_modulename(filepath: str) -> str:
    """Used to convert a an app ref passed in as a filepath to a module"""
    module = filepath.removesuffix(".py")
    return module.replace("/", ".")
