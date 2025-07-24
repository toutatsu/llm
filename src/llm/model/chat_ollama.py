from langchain_ollama import ChatOllama

llm_model_name = "gemma3:1b"

llm = ChatOllama(
    base_url="http://ollama:11434",
    model=llm_model_name,
    verbose=True,
    temperature=0.6,
    keep_alive=True,
    num_ctx=40000,
)
