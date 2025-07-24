from chat_ollama import llm


def stream_response(prompt: str):
    for chunk in llm.stream(prompt):
        print(chunk.content, end="", flush=True)


if __name__ == "__main__":
    stream_response("Explain how AI works in a few words")