FROM python:latest

WORKDIR /home/llm/

# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# RUN uv sync
# RUN uv pip install -e .

# RUN apt-get update --assume-yes && apt-get upgrade --assume-yes
