import logging
import sys

logger = logging.getLogger(__name__)


def set_recursion_limit():
    sys.setrecursionlimit(10**9)
    if sys.platform == "linux":
        import resource
        logger.info(f"Setting stack limit to {resource.RLIM_INFINITY}")
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
