# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

# Copy project metadata first and resolve dependencies for Linux inside the image
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    sh -lc 'uv sync --no-install-project --no-dev'

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    sh -lc 'uv sync --no-dev'

ENV PATH="/app/.venv/bin:$PATH"

CMD ["mcp-server-snowflake", "--service-config-file", "/app/services/tools_config.yaml", "--transport", "streamable-http"]
