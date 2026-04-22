import os

from langchain.chat_models import init_chat_model

_LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3.5:35b-cloud")
_LLM_PROVIDER = os.environ.get("LLM_MODEL_PROVIDER", "ollama")
_VLM_MODEL = os.environ.get("VLM_MODEL", "gemma4:27b-cloud")
_VLM_PROVIDER = os.environ.get("VLM_MODEL_PROVIDER", "ollama")


def get_chat_model(model: str | None = None, model_provider: str | None = None):
    model = model or _LLM_MODEL
    model_provider = model_provider or _LLM_PROVIDER
    kwargs = {
        "base_url": "https://ollama.com",
        "verbose": True,
    }
    return init_chat_model(model=model, model_provider=model_provider, **kwargs)


def get_vlm_chat_model():
    """VLM_MODEL / VLM_MODEL_PROVIDER 環境変数で指定されたビジョン対応モデルを返す。"""
    return get_chat_model(model=_VLM_MODEL, model_provider=_VLM_PROVIDER)


if __name__ == "__main__":
    chat_model = get_chat_model()
    print(chat_model.invoke("test"))
