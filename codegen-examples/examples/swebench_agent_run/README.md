# SWE-bench Agent Runner

Tool for running and evaluating model fixes using SWE-bench.

## Setup

1. Using the `.env.template` reference, create a `.env` file in the project root and add your API keys:

   ```env
   OPENAI_API_KEY=your_key_here
   MODAL_TOKEN_ID=your_token_id
   MODAL_TOKEN_SECRET=your_token_secret
   ```

1. Create and activate a virtual environment:

   ```bash
   uv venv
   source .venv/bin/activate
   ```

1. Install the package:

   ```bash
   # Basic installation
   uv pip install -e .

   # With metrics support
   uv pip install -e ".[metrics]"

   # With development tools
   uv pip install -e ".[dev]"

   # Install everything
   uv pip install -e ".[all]"
   ```

1. Set up Modal:

   - Create an account at https://modal.com/ if you don't have one
   - Activate your Modal profile:
     ```bash
     python -m modal profile activate <profile_name>
     ```

## Usage

The package provides two main command-line tools:

### Testing SWE CodeAgent

Run the agent on a specific repository:

```bash
# Using the installed command
swe-agent --repo pallets/flask --prompt "Analyze the URL routing system"

# Options
swe-agent --help
Options:
  --agent-class [DefaultAgent|CustomAgent]  Agent class to use
  --repo TEXT                               Repository to analyze (owner/repo)
  --prompt TEXT                             Prompt for the agent
  --help                                    Show this message and exit
```

### Running SWE-Bench Eval

Deploy modal app

```bash
./deploy.sh
```

Run evaluations on model fixes:

```bash
# Using the installed command
swe-eval --dataset lite --length 10

# Options
swe-eval --help
Options:
  --use-existing-preds TEXT      Run ID of existing predictions
  --dataset [lite|full|verified|lite_small|lite_medium|lite_large]
  --length INTEGER               Number of examples to process
  --instance-id TEXT             Specific instance ID to process
  --repo TEXT                    Specific repo to evaluate
  --local                        Run evaluation locally
  --instance-ids LIST_OF_STRINGS  The instance IDs of the examples to process.
                                  Example: --instance-ids <instance_id1>,<instance_id2>,...
  --push-metrics                 Push results to metrics database (Requires additional database environment variables)
  --help                         Show this message and exit
```
