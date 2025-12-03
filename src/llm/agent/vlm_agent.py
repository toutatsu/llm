# https://docs.langchain.com/oss/python/langchain/agents
import base64
import requests
from langchain.agents import create_agent

from llm.chat_models import get_chat_model


def get_base64_from_image_url(url: str) -> str:
    """
    Convert an image URL to a base64-encoded string.
    Args:
        url (str): The URL of the image.
    Returns:
        str: The base64-encoded string of the image.
    """
    image_bytes = requests.get(url).content
    return base64.b64encode(image_bytes).decode("utf-8")

# TODO
def get_image_message(image_list: list[str]):
    """Get image content as a base64-encoded string."""

    return (
        [
            {"type": "text", "text": f"image: {image_list[0]}"},
            {
                "type": "image",
                "source_type": "base64",
                "mime_type": "image/jpeg",
                "data": get_base64_from_image_url(image_list[0]),
            },
        ],
    )


def get_vlm_agent():
    vlm_agent = create_agent(model=get_chat_model(), tools=[get_image_message])
    return vlm_agent


if __name__ == "__main__":

    image_url = ""

    vlm_agent = get_vlm_agent()

    print(
        vlm_agent.invoke(
            input={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "次の画像を説明して：",
                            },
                            # {
                            #     "type": "image_url",
                            #     "image_url": get_base64_from_image_url(image_url),
                            # },
                            {
                                "type": "image",
                                "source_type": "base64",
                                "mime_type": "image/jpeg",
                                "data": f"{get_base64_from_image_url(image_url)}",
                            },
                        ],
                    }
                ]
            }
        )
    )
