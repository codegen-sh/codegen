from itertools import batched
from typing import Iterator, List, TypeVar

from tqdm import tqdm

T = TypeVar("T")


def track_batches(
    items: List[T], batch_size: int, desc: str = "Processing"
) -> Iterator[tuple[int, List[T]]]:
    """
    Track batch progress with tqdm.
    Returns tuples of (batch_number, batch_items).
    """
    total_items = len(items)
    total_batches = (total_items + batch_size - 1) // batch_size

    with tqdm(
        total=total_items,
        desc=desc,
        unit="examples",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} examples [{elapsed}<{remaining}, {rate_fmt}]",
    ) as pbar:
        for batch_num, batch in enumerate(batched(items, batch_size), 1):
            pbar.set_postfix({"batch": f"{batch_num}/{total_batches}", "batch_size": len(batch)})
            yield batch_num, batch
            pbar.update(len(batch))
