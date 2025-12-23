# https://docs.langchain.com/oss/python/langchain/agents
import base64
import requests
from langchain.agents import create_agent

from llm.chat_models import get_chat_model
from llm.logger import logger


def get_base64_from_image_url(url: str) -> str:
    """
    Convert an image URL to a base64-encoded string.
    Args:
        url (str): The URL of the image.
    Returns:
        str: The base64-encoded string of the image.
    """

    # logger.debug(f"{url}")

    image_bytes = requests.get(url).content
    return base64.b64encode(image_bytes).decode("utf-8")

def get_image_message(image_list: list[str]):
    """Get image content as a base64-encoded string."""
    # https://docs.langchain.com/oss/python/langchain/messages#multimodal

    image_message_list = []

    for image in image_list:
        # image_message_list.append(
        #     {"type": "text", "text": f"画像データ: {image}"},
        # )
        image_message_list.append(
            # # from URL
            # {
            #     "type": "image",
            #     "url": image
            # }

            # from base64 data
            {
                "type": "image",
                "base64": get_base64_from_image_url(image),
                "mime_type": "image/jpeg",
            }
        )

    return image_message_list


VLM_AGENT_SYSTEM_PROMPT = """あなたはユーザからの指示に基づいて画像を確認するvlm_agentです。
必要に応じてツールを実行し、与えられた画像について正確な情報を出力してください。
"""

def get_vlm_agent():
    vlm_agent = create_agent(
        model=get_chat_model(
            model_provider="ollama",
            model="ministral-3:14b-cloud",
        ),
        tools=[get_image_message],
        system_prompt=VLM_AGENT_SYSTEM_PROMPT,
    )
    return vlm_agent


if __name__ == "__main__":

    image_url = ""

    vlm_agent = get_vlm_agent()

    # print(
    #     vlm_agent.invoke(
    #         input={
    #             "messages": [
    #                 {
    #                     "role": "user",
    #                     "content": [
    #                         {
    #                             "type": "text",
    #                             "text": "次の画像を説明して：",
    #                         },
    #                         # {
    #                         #     "type": "image_url",
    #                         #     "image_url": get_base64_from_image_url(image_url),
    #                         # },
    #                         {
    #                             "type": "image",
    #                             "source_type": "base64",
    #                             "mime_type": "image/jpeg",
    #                             "data": f"{get_base64_from_image_url(image_url)}",
    #                         },
    #                     ],
    #                 }
    #             ]
    #         }
    #     )
    # )
