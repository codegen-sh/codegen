# Install uv
FROM python:3.12-slim AS installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Change the working directory to the `app` directory
WORKDIR /app

# Copy the lockfile and `pyproject.toml` into the image
COPY uv.lock /app/uv.lock
COPY pyproject.toml /app/pyproject.toml

# Install dependencies
RUN apt-get update && apt-get install -y git \
    && uv sync --frozen --no-install-project \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


FROM python:3.12-slim

ENV PATH="/venv/bin:/app/scripts:$PATH"
# Copy the project into the image
COPY --from=installer /app/.venv/ /venv

RUN apt-get update && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


WORKDIR /app

COPY . .

CMD ["python", "modal_run.py"]
