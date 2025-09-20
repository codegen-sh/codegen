from codegen.cli.env.enums import Environment
from codegen.cli.env.global_env import global_env


def get_modal_workspace():
    match global_env.ENV:
        case Environment.PRODUCTION:
            return "codegen-sh"
        case Environment.STAGING:
            return "codegen-sh-staging"
        case Environment.DEVELOP:
            return "codegen-sh-develop"
        case _:
            msg = f"Invalid environment: {global_env.ENV}"
            raise ValueError(msg)


def get_modal_prefix():
    workspace = get_modal_workspace()
    if global_env.ENV == Environment.DEVELOP and global_env.MODAL_ENVIRONMENT:
        return f"{workspace}-{global_env.MODAL_ENVIRONMENT}"
    return workspace


MODAL_PREFIX = get_modal_prefix()
