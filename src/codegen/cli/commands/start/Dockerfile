FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set environment variables to prevent interactive prompts during installation
ENV NVM_DIR=/root/.nvm \
    NODE_VERSION=18.17.0 \
    DEBIAN_FRONTEND=noninteractive \
    NODE_OPTIONS="--max-old-space-size=8192" \
    PYTHONUNBUFFERED=1 \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    PYTHONPATH="/usr/local/lib/python3.13/site-packages" \
    IS_SANDBOX=True \
    HATCH_BUILD_HOOKS_ENABLE=1

# Update packages lists and install git and curl
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gcc \
    build-essential \
    python3-dev \
    # Cleanup apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Install nvm and Node.js
SHELL ["/bin/bash", "-c"]
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash \
    && source $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm use default \
    && npm install -g yarn pnpm \
    && corepack enable \
    && corepack prepare yarn@stable --activate \
    && corepack prepare pnpm@latest --activate \
    && uv pip install --system uvicorn[standard]

# Add node and npm to PATH
ENV PATH=$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH
RUN node --version \
    && corepack --version \
    && npm --version \
    && yarn --version \
    && pnpm --version \
    && python --version

# Add build argument for codegen version and build type
ARG CODEGEN_VERSION
ARG BUILD_TYPE="release"  # Can be "release" or "dev"

# Install codegen based on BUILD_TYPE
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=.,target=/codegen-sdk,rw \
    if [ "$BUILD_TYPE" = "release" ]; then \
        uv pip install --system codegen==${CODEGEN_VERSION}; \
    else \
        cd /codegen-sdk \
        && uv venv && source .venv/bin/activate \
        && uv sync --frozen --no-dev --all-extras \
        && uv pip install --system -e . --no-deps \
        && uv pip install --system .; \
    fi

RUN codegen --version

# Create a non-root user for local development + debugging
RUN useradd -m -s /bin/bash user
USER root
RUN chown -R user:user /home/user
USER user

WORKDIR /app
ENTRYPOINT ["/bin/bash", "-c"]
