# Overview

The **Codegen on OSS** package provides a modular pipeline that:

- **Collects repository URLs** from different sources (e.g., CSV files or GitHub searches).
- **Parses repositories** using the codegen tool.
- **Profiles performance** and logs metrics for each parsing run.
- **Logs errors** to help pinpoint parsing failures or performance bottlenecks.

______________________________________________________________________

## Package Structure

The package is composed of several modules:

- `sources`

  - Defines the Repository source classes and settings. Settings are all configurable via environment variables

  - Github Source

    ```python
    class GithubSettings(SourceSettings):
        language: Literal["python", "typescript"] = "python"
        heuristic: Literal[
            "stars",
            "forks",
            "updated",
            # "watchers",
            # "contributors",
            # "commit_activity",
            # "issues",
            # "dependency",
        ] = "stars"
        github_token: str | None = None
    ```

    - The three options available now are the three supported by the Github API.
      - Future Work Additional options will require different strategies

  - CSV Source

    - Simply reads repo URLs from CSV

- `cache`

  - Currently only specifies the cache directory. It is used for caching git repositories pulled by the pipeline `--force-pull` can be used to re-pull from the remote.

- `cli`

  - Built with Click, the CLI provides two main commands:
    - `run-one`: Parses a single repository specified by URL.
    - `run`: Iterates over repositories obtained from a selected source and parses each one.

- **`metrics`**

  - Provides profiling tools to measure performance during the parse:
    - `MetricsProfiler`: A context manager that creates a profiling session.
    - `MetricsProfile`: Represents a "span" or a "run" of a specific repository. Records step-by-step metrics (clock duration, CPU time, memory usage) and writes them to a CSV file specified by `--output-path`

- **`parser`**

  Contains the `CodegenParser` class that orchestrates the parsing process:

  - Clones the repository (or forces a pull if specified).
  - Initializes a `Codebase` (from the codegen tool).
  - Runs post-initialization validation.
  - Integrates with the `MetricsProfiler` to log measurements at key steps.

______________________________________________________________________

## Getting Started

1. **Configure the Repository Source**

   Decide whether you want to read from a CSV file or query GitHub:

   - For CSV, ensure that your CSV file (default: `input.csv`) exists and contains repository URLs in its first column \[`repo_url`\] and commit hash \[`commit_hash`\] (or empty) in the second column.
   - For GitHub, configure your desired settings (e.g., `language`, `heuristic`, and optionally a GitHub token) via environment variables (`GITHUB_` prefix)

1. **Run the Parser**

   Use the CLI to start parsing:

   - To parse one repository:

     ```bash
     uv run cgparse run-one --help
     ```

   - To parse multiple repositories from a source:

     ```bash
     uv run cgparse run --help
     ```

1. **Review Metrics and Logs**

   After parsing, check the CSV (default: `metrics.csv` ) to review performance measurements per repository. Error logs are written to the specified error output file (default: `errors.log`)

______________________________________________________________________

## Running on Modal

```shell
$ uv run modal run modal_run.py
```

Codegen runs this parser on modal using the CSV source file `input.csv` tracked in this repository.

### Modal Configuration

- **Compute Resources**: Allocates 4 CPUs and 16GB of memory.
- **Secrets & Volumes**: Uses secrets (for bucket credentials) and mounts a volume for caching repositories.
- **Image Setup**: Builds on a Debian slim image with Python 3.12, installs required packages (`uv` and `git` )
- **Environment Configuration**: Environment variables (e.g., GitHub settings) are injected at runtime.

The function `parse_repo_on_modal` performs the following steps:

1. **Environment Setup**: Updates environment variables and configures logging using Loguru.
1. **Source Initialization**: Creates a repository source based on the provided type (e.g., GitHub).
1. **Metrics Profiling**: Instantiates `MetricsProfiler` to capture and log performance data.
1. **Repository Parsing**: Iterates over repository URLs and parses each using the `CodegenParser`.
1. **Error Handling**: Logs any exceptions encountered during parsing.
1. **Result Upload**: Uses the `BucketStore` class to upload the configuration, logs, and metrics to an S3 bucket.

### Bucket Storage

**Bucket (public):** [codegen-oss-parse](https://s3.amazonaws.com/codegen-oss-parse/)

The results of each run are saved under the version of `codegen` lib that the run installed and the source type it was run with. Within this prefix:

- Source Settings
  - `https://s3.amazonaws.com/codegen-oss-parse/{version}/{source}/config.json`
- Metrics
  - `https://s3.amazonaws.com/codegen-oss-parse/{version}/{source}/metrics.csv`
- Logs
  - `https://s3.amazonaws.com/codegen-oss-parse/{version}/{source}/output.logs`

______________________________________________________________________

### Running it yourself

You can also run `modal_run.py` yourself. It is designed to be run via Modal for cloud-based parsing. It offers additional configuration methods:

```shell
$ uv run modal run modal_run.py
```

- **CSV and Repository Volumes:**
  The script defines two Modal volumes:

  - `codegen-oss-input-volume`: For uploading and reloading CSV inputs.
  - `codegen-oss-repo-volume`: For caching repository data during parsing.
    The repository and input volume names are configurable via environment variables (`CODEGEN_MODAL_REPO_VOLUME` and `CODEGEN_MODAL_INPUT_VOLUME`).

- **Secrets Handling:**
  The script loads various credentials via Modal secrets. It first checks for a pre-configured Modal secret (`codegen-oss-bucket-credentials` configurable via environment variable `CODEGEN_MODAL_SECRET_NAME`) and falls back to dynamically created Modal secret from local `.env` or environment variables if not found.

- **Entrypoint Parameters:**
  The main function supports multiple source types:

  - **csv:** Uploads a CSV file (`--csv-file input.csv`) for batch processing.
  - **single:** Parses a single repository specified by its URL (`--single-url "https://github.com/codegen-sh/codegen-sdk.git"`) and an optional commit hash (`--single-commit ...`)
  - **github:** Uses GitHub settings, language (`--github-language python`) and heuristic (`--github-heuristic stars`) to query for top repositories.

- **Result Storage:**
  Upon completion, logs and metrics are automatically uploaded to the S3 bucket specified by the environment variable `BUCKET_NAME` (default: `codegen-oss-parse`). This allows for centralized storage and easy retrieval of run outputs. The AWS Credentials provided in the secret are used for this operation.

______________________________________________________________________

## Extensibility

**Adding New Sources:**

You can define additional repository sources by subclassing `RepoSource` and providing a corresponding settings class. Make sure to set the `source_type` and register your new source by following the pattern established in `CSVInputSource` or `GithubSource`.

**Improving Testing:**

The detailed metrics collected can help you understand where parsing failures occur or where performance lags. Use these insights to improve error handling and optimize the codegen parsing logic.

**Containerization and Automation:**

There is a Dockerfile that can be used to create an image capable of running the parse tests. Runtime environment variables can be used to configure the run and output.

**Input & Configuration**

Explore a better CLI for providing options to the Modal run.

______________________________________________________________________

## Example Log Output

```shell
[codegen-on-oss*] codegen/codegen-on-oss/$ uv run cgparse run --source csv
 21:32:36 INFO Cloning repository https://github.com/JohnSnowLabs/spark-nlp.git
 21:36:57 INFO {
    "profile_name": "https://github.com/JohnSnowLabs/spark-nlp.git",
    "step": "codebase_init",
    "delta_time": 7.186550649999845,
    "cumulative_time": 7.186550649999845,
    "cpu_time": 180.3553702,
    "memory_usage": 567525376,
    "memory_delta": 317095936,
    "error": null
}
 21:36:58 INFO {
    "profile_name": "https://github.com/JohnSnowLabs/spark-nlp.git",
    "step": "post_init_validation",
    "delta_time": 0.5465090990001045,
    "cumulative_time": 7.733059748999949,
    "cpu_time": 180.9174761,
    "memory_usage": 569249792,
    "memory_delta": 1724416,
    "error": null
}
 21:36:58 ERROR Repository: https://github.com/JohnSnowLabs/spark-nlp.git
Traceback (most recent call last):

  File "/home/codegen/codegen/codegen-on-oss/.venv/bin/cgparse", line 10, in <module>
    sys.exit(cli())
    │   │    └ <Group cli>
    │   └ <built-in function exit>
    └ <module 'sys' (built-in)>
  File "/home/codegen/codegen/codegen-on-oss/.venv/lib/python3.12/site-packages/click/core.py", line 1161, in __call__
    return self.main(*args, **kwargs)
           │    │     │       └ {}
           │    │     └ ()
           │    └ <function BaseCommand.main at 0x7f4665c15120>
           └ <Group cli>
  File "/home/codegen/codegen/codegen-on-oss/.venv/lib/python3.12/site-packages/click/core.py", line 1082, in main
    rv = self.invoke(ctx)
         │    │      └ <click.core.Context object at 0x7f4665f3c9e0>
         │    └ <function MultiCommand.invoke at 0x7f4665c16340>
         └ <Group cli>
  File "/home/codegen/codegen/codegen-on-oss/.venv/lib/python3.12/site-packages/click/core.py", line 1697, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
           │               │       │       │      └ <click.core.Context object at 0x7f4665989b80>
           │               │       │       └ <function Command.invoke at 0x7f4665c15d00>
           │               │       └ <Command run>
           │               └ <click.core.Context object at 0x7f4665989b80>
           └ <function MultiCommand.invoke.<locals>._process_result at 0x7f466597fb00>
  File "/home/codegen/codegen/codegen-on-oss/.venv/lib/python3.12/site-packages/click/core.py", line 1443, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           │   │      │    │           │   └ {'source': 'csv', 'output_path': 'metrics.csv', 'error_output_path': 'errors.log', 'cache_dir': PosixPath('/home/.cache...
           │   │      │    │           └ <click.core.Context object at 0x7f4665989b80>
           │   │      │    └ <function run at 0x7f466145eac0>
           │   │      └ <Command run>
           │   └ <function Context.invoke at 0x7f4665c14680>
           └ <click.core.Context object at 0x7f4665989b80>
  File "/home/codegen/codegen/codegen-on-oss/.venv/lib/python3.12/site-packages/click/core.py", line 788, in invoke
    return __callback(*args, **kwargs)
                       │       └ {'source': 'csv', 'output_path': 'metrics.csv', 'error_output_path': 'errors.log', 'cache_dir': PosixPath('/home/.cache...
                       └ ()

  File "/home/codegen/codegen/codegen-on-oss/codegen_on_oss/cli.py", line 121, in run
    parser.parse(repo_url)
    │      │     └ 'https://github.com/JohnSnowLabs/spark-nlp.git'
    │      └ <function CodegenParser.parse at 0x7f4664b014e0>
    └ <codegen_on_oss.parser.CodegenParser object at 0x7f46612def30>

  File "/home/codegen/codegen/codegen-on-oss/codegen_on_oss/parser.py", line 52, in parse
    with self.metrics_profiler.start_profiler(
         │    │                └ <function MetricsProfiler.start_profiler at 0x7f466577d760>
         │    └ <codegen_on_oss.metrics.MetricsProfiler object at 0x7f465e6c2e70>
         └ <codegen_on_oss.parser.CodegenParser object at 0x7f46612def30>

  File "/home/.local/share/uv/python/cpython-3.12.6-linux-x86_64-gnu/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
    │    │   │     └ ParseRunError(<PostInitValidationStatus.LOW_IMPORT_RESOLUTION_RATE: 'LOW_IMPORT_RESOLUTION_RATE'>)
    │    │   └ <method 'throw' of 'generator' objects>
    │    └ <generator object MetricsProfiler.start_profiler at 0x7f4660478740>
    └ <contextlib._GeneratorContextManager object at 0x7f46657849e0>

> File "/home/codegen/codegen/codegen-on-oss/codegen_on_oss/metrics.py", line 41, in start_profiler
    yield profile
          └ <codegen_on_oss.metrics.MetricsProfile object at 0x7f4665784a10>

  File "/home/codegen/codegen/codegen-on-oss/codegen_on_oss/parser.py", line 64, in parse
    raise ParseRunError(validation_status)
          │             └ <PostInitValidationStatus.LOW_IMPORT_RESOLUTION_RATE: 'LOW_IMPORT_RESOLUTION_RATE'>
          └ <class 'codegen_on_oss.parser.ParseRunError'>

codegen_on_oss.parser.ParseRunError: LOW_IMPORT_RESOLUTION_RATE
 21:36:58 INFO {
    "profile_name": "https://github.com/JohnSnowLabs/spark-nlp.git",
    "step": "TOTAL",
    "delta_time": 7.740976418000173,
    "cumulative_time": 7.740976418000173,
    "cpu_time": 180.9221699,
    "memory_usage": 569249792,
    "memory_delta": 0,
    "error": "LOW_IMPORT_RESOLUTION_RATE"
}
 21:36:58 INFO Cloning repository https://github.com/Lightning-AI/lightning.git
 21:37:53 INFO {
    "profile_name": "https://github.com/Lightning-AI/lightning.git",
    "step": "codebase_init",
    "delta_time": 24.256577352999557,
    "cumulative_time": 24.256577352999557,
    "cpu_time": 211.3604081,
    "memory_usage": 1535971328,
    "memory_delta": 966184960,
    "error": null
}
 21:37:53 INFO {
    "profile_name": "https://github.com/Lightning-AI/lightning.git",
    "step": "post_init_validation",
    "delta_time": 0.137609629000508,
    "cumulative_time": 24.394186982000065,
    "cpu_time": 211.5082702,
    "memory_usage": 1536241664,
    "memory_delta": 270336,
    "error": null
}
 21:37:53 INFO {
    "profile_name": "https://github.com/Lightning-AI/lightning.git",
    "step": "TOTAL",
    "delta_time": 24.394700584999555,
    "cumulative_time": 24.394700584999555,
    "cpu_time": 211.5088282,
    "memory_usage": 1536241664,
    "memory_delta": 0,
    "error": null
}
```

## Example Metrics Output

| profile_name           | step                 | delta_time         | cumulative_time    | cpu_time    | memory_usage | memory_delta | error                      |
| ---------------------- | -------------------- | ------------------ | ------------------ | ----------- | ------------ | ------------ | -------------------------- |
| JohnSnowLabs/spark-nlp | codebase_init        | 7.186550649999845  | 7.186550649999845  | 180.3553702 | 567525376    | 317095936    |                            |
| JohnSnowLabs/spark-nlp | post_init_validation | 0.5465090990001045 | 7.733059748999949  | 180.9174761 | 569249792    | 1724416      |                            |
| JohnSnowLabs/spark-nlp | TOTAL                | 7.740976418000173  | 7.740976418000173  | 180.9221699 | 569249792    | 0            | LOW_IMPORT_RESOLUTION_RATE |
| Lightning-AI/lightning | codebase_init        | 24.256577352999557 | 24.256577352999557 | 211.3604081 | 1535971328   | 966184960    |                            |
| Lightning-AI/lightning | post_init_validation | 0.137609629000508  | 24.394186982000065 | 211.5082702 | 1536241664   | 270336       |                            |
| Lightning-AI/lightning | TOTAL                | 24.394700584999555 | 24.394700584999555 | 211.5088282 | 1536241664   | 0            |                            |
