import os
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from dataclasses import dataclass

load_dotenv()


@dataclass
class XAIClient:
    api_key: str = os.getenv("XAI_API_KEY")
    base_url: str = "https://api.x.ai/v1"

    def __post_init__(self):
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=3600,
        )
    
    def get_response(self, model: str, messages: list = None):
        """
        Get a response from the Grok AI model.

        :param model: The Grok model to use (e.g., 'grok-3').
        :param messages: The input messages for the AI model.
        :return: The response content from the AI model.
        """
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            return completion.choices[0].message.content

        except Exception as e:
            print(f"Error: {e}")
    
    def get_structured_response(self, model: str, response_format: BaseModel = None, content: str = None):
        """
        Get a structured output response from the Grok AI api.

        :param model: The Grok model to use (e.g., 'grok-3').
        :param messages: The input messages for the AI model.
        :param response_format: The Pydantic model to define the structure of the response.
        """
        messages = [
            {
                "role": "system",
                "content": "Extract structured information from the content."
            },
            {
                "role": "user",
                "content": content
            }
        ]

        try:
            completion = self.client.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=response_format,
            )
            return completion.choices[0].message.parsed
        
        except Exception as e:
            print(f"Error: {e}")
