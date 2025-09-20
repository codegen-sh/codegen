def list_to_comma_separated(items: list[str]) -> str:
    """Given a list of items, returns a comma separated string of the items"""
    return ",".join(items)


def comma_separated_to_list(comma_separated: str) -> list[str]:
    """Given a comma separated string, returns a list of the comma separated items.
    Strips whitespace from each item, drops any items that are whitespace only
    """
    items = comma_separated.split(",") if comma_separated else []
    non_empty_items = [item.strip() for item in items if item.strip()]
    return non_empty_items


def comma_separated_to_set(comma_separated: str) -> set[str]:
    """Given a comma separated string, returns a set of the comma separated items.
    Strips whitespace from each item, drops any items that are whitespace only
    """
    items = comma_separated.split(",") if comma_separated else []
    non_empty_items = {item.strip() for item in items if item.strip()}
    return non_empty_items
