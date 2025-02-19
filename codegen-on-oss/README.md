# codegen-on-oss

[![Release](https://img.shields.io/github/v/release/clee-codegen/codegen-on-oss)](https://img.shields.io/github/v/release/clee-codegen/codegen-on-oss)
[![Build status](https://img.shields.io/github/actions/workflow/status/clee-codegen/codegen-on-oss/main.yml?branch=main)](https://github.com/clee-codegen/codegen-on-oss/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/clee-codegen/codegen-on-oss/branch/main/graph/badge.svg)](https://codecov.io/gh/clee-codegen/codegen-on-oss)
[![Commit activity](https://img.shields.io/github/commit-activity/m/clee-codegen/codegen-on-oss)](https://img.shields.io/github/commit-activity/m/clee-codegen/codegen-on-oss)
[![License](https://img.shields.io/github/license/clee-codegen/codegen-on-oss)](https://img.shields.io/github/license/clee-codegen/codegen-on-oss)

Testing codegen parsing on popular OSS repositories

- **Github repository**: <https://github.com/clee-codegen/codegen-on-oss/>
- **Documentation** <https://clee-codegen.github.io/codegen-on-oss/>

### Set Up Your Development Environment

install the environment and the pre-commit hooks with

```bash
make install
```

This will also generate your `uv.lock` file

### pre-commit hooks

```bash
uv run pre-commit run -a
```

______________________________________________________________________

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
