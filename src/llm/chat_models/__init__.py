from langchain.chat_models import init_chat_model


def get_chat_model():

    # https://reference.langchain.com/python/langchain/models/#langchain.chat_models.init_chat_model

    # local ollama
    model="gemma3:1b"
    model_provider="openai"
    kwargs = {
        "base_url": "http://ollama:11434/v1",
        "verbose":True,
        "api_key":"dummy",
    }

    # # ollama Cloud models
    # # https://ollama.com/blog/cloud-models
    # model = "gpt-oss:20b-cloud"
    # model_provider = "ollama"
    # kwargs = {
    #     "base_url": "https://ollama.com",
    #     "verbose": True,
    # }

    # # google genai
    # model="gemini-2.5-flash"
    # model_provider="google_genai"
    # kwargs = {}

    chat_model = init_chat_model(
        model=model,
        model_provider=model_provider,
        **kwargs,
    )

    return chat_model


if __name__ == "__main__":
    chat_model = get_chat_model()
    print(chat_model.invoke("test"))
