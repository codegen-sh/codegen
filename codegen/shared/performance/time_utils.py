import datetime as dt

import humanize


def humanize_duration(seconds: float) -> str:
    """Converts a duration in seconds to a human-readable string.
    Example: humanize_duration(60) -> "1 minute"
    """
    delta = dt.timedelta(seconds=seconds)
    return humanize.precisedelta(delta, minimum_unit="milliseconds")
