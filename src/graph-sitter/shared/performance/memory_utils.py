import os
from dataclasses import dataclass

import psutil


@dataclass
class MemoryStats:
    memory_rss_gb: float
    memory_vms_gb: float


def get_memory_stats() -> MemoryStats:
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return MemoryStats(
        memory_rss_gb=memory_info.rss / 1024 / 1024 / 1024,
        memory_vms_gb=memory_info.vms / 1024 / 1024 / 1024,
    )
