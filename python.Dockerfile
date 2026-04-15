FROM python:latest

# ホスト側のUID/GIDに合わせてユーザーを作成する
# compose.python.yaml の build.args から渡す（デフォルト: 1000）
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid ${USER_GID} llm \
    && useradd --uid ${USER_UID} --gid ${USER_GID} \
               --shell /bin/bash --create-home llm

# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /home/llm/

# RUN uv sync
# RUN uv pip install -e .

# RUN apt-get update --assume-yes && apt-get upgrade --assume-yes

USER llm
