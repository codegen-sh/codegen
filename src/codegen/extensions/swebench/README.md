## Codegen Harness and Evaluator for SWE Bennch Development Tool

This folder contains a harness and evaluator for the SWE Bench leaderboard, and enables developers to test and evaluate their codegen models on the SWE Bench leaderboard.

It integrates directly into the Codegen agentic framework and can be built on top of.

### Setup

Remember to install all the dependencies for the environment.

### Usage

#### Edit agent.py, your codegen agent

This file contains the main logic for the agent.

The agent taps into the tree sitter using codegen. You can modify this by adding additional tools, extending its capabilities, prompts, and more.

It is invoked in the harness script.

#### Run harness.py to run the agent

This script will gather the correct dataset, run the agent, and save the results.

#### Run report.py to generate a report

This script will generate a report from the results. It will loop through all the results and generate a report to evaluate each. Currently, there is an error in the docker image.

There are currently example predictions in the `predictions/results` folder.
