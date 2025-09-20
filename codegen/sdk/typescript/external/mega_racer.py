from py_mini_racer import MiniRacer, init_mini_racer
from py_mini_racer._context import Context
from py_mini_racer._set_timeout import INSTALL_SET_TIMEOUT


class MegaRacer(MiniRacer):
    """MegaRacer is a patch on MiniRacer that allows for more memory.

    Original MiniRacer:
        MiniRacer evaluates JavaScript code using a V8 isolate.

        A MiniRacer instance can be explicitly closed using the close() method, or by using
        the MiniRacer as a context manager, i.e,:

        with MiniRacer() as mr:
            ...

        The MiniRacer instance will otherwise clean up the underlying V8 resource upon
        garbage collection.

    Attributes:
        json_impl: JSON module used by helper methods default is
            [json](https://docs.python.org/3/library/json.html)
    """

    def __init__(self) -> None:
        # Set the max old space size to 64GB
        dll = init_mini_racer(ignore_duplicate_init=True, flags=["--max-old-space-size=65536"])
        self._ctx = Context(dll)
        self.eval(INSTALL_SET_TIMEOUT)
