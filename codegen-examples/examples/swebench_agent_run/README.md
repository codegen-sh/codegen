# INSTRUCTIONS

1. Create a `.env` file in the root directory and add your API keys.
1. cd into the `examples/swebench_agent_run` directory
1. Create a `.venv` with `uv venv` and activate it with `source .venv/bin/activate`
1. Install the codegen dependencies with `uv pip install -e ../../../`
1. Activate the appropriate modal environment.
1. Launch the modal app with `uv run modal deploy --env=<env_name> webhooks.py`
1. Run the script with `python eval_run.py`
