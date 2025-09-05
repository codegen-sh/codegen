from enum import Enum


class SWEBenchDataset(Enum):
    LITE = "princeton-nlp/SWE-bench_Lite"
    FULL = "princeton-nlp/SWE-bench"
    VERIFIED = "princeton-nlp/SWE-bench-verified"


class SWEBenchLiteSubset(Enum):
    LITE_SMALL = "lite_small"
    LITE_MEDIUM = "lite_medium"
    LITE_LARGE = "lite_large"
