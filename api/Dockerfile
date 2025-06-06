FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# install uv
# see: https://docs.astral.sh/uv/guides/integration/docker/
COPY --from=ghcr.io/astral-sh/uv:0.7.10 /uv /uvx /bin/

ENV PATH="/app/.venv/bin:${PATH}"

# compiling Python source files to bytecode to improve startup time
# see: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv cache
# see: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# install deps
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONAPP=/app

COPY . /app

# sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

EXPOSE 8123

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8123", "app.main:app"]
