# INSTRUCTIONS

1. Create a `.env` file in the `swebench_agent_run` directory (codegen-examples/examples/swebench_agent_run) and add your API keys.

1. cd into the `codegen-examples/examples/swebench_agent_run` directory

1. Create a `.venv` with `uv venv` and activate it with `source .venv/bin/activate`

1. Install the dependencies with `uv pip install .`

1. Install the codegen dependencies with `uv add codegen`

- Note: If you'd like to install the dependencies using the global environment, use `uv pip install -e ../../../` instead of `uv pip install .`. This will allow you to test modifications to the codegen codebase. You will need to run `uv pip install -e ../../../` each time you make changes to the codebase.

6. Ensure that you have a modal account and profile set up. If you don't have one, you can create one at https://modal.com/

1. Activate the appropriate modal profile `python -m modal profile activate <profile_name>`

1. Launch the modal app with `python -m modal deploy --env=<env_name> entry_point.py`

1. Run the evaluation with `python -m run_eval` with the desired options:

- ```bash
  $ python run_eval.py --help
  Usage: run_eval.py [OPTIONS]

  Options:
  --use-existing-preds TEXT       The run ID of the existing predictions to
                                  use.
  --dataset [lite|full|verified|lite_small|lite_medium|lite_large]
                                  The dataset to use.
  --length INTEGER                The number of examples to process.
  --instance-id TEXT              The instance ID of the example to process.
  --repo TEXT                     The repo to use.
  --instance-ids LIST_OF_STRINGS  The instance IDs of the examples to process.
                                  Example: --instance-ids <instance_id1>,<instance_id2>,...
  --help                          Show this message and exit.
  ```
