from enum import Enum

from bar.enums import Char


class Bar(Enum):
    BAR = 1
    CHAR = 2


def bar():
    return Bar.BAR + Char.BAR
