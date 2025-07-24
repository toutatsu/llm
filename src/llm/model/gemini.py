# https://ai.google.dev/gemini-api/docs/quickstart?hl=ja

from google import genai

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

# # Generate a response
# response = client.models.generate_content(
#     model="gemini-2.5-flash", contents="Explain how AI works in a few words"
# )
# print(response.text)

from time import sleep
# Streaming response
for chunk in client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words as long as possible",
):
    print(chunk.text, end="|", flush=True)
    sleep(1)


# # https://python.langchain.com/docs/integrations/chat/google_generative_ai/
# import getpass
# import os

# if "GOOGLE_API_KEY" not in os.environ:
#     os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

# from langchain_google_genai import ChatGoogleGenerativeAI

# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     # other params...
# )
