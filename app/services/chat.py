from fastapi import HTTPException
from openai import OpenAI

from app.config import settings

MODEL = "z-ai/glm-4.5-air:free"

prompt_template = """You are a demo assistant for PyBAQ (Python Barranquilla community) that provides detailed answers to user questions.
When you receive a question, you should:
1. Analyze the question and identify key components.
2. Provide a comprehensive answer based on the information available.
3. If you need to make assumptions, clearly state them in your answer.
4. Always aim to provide the most accurate and helpful response possible.
Here is the user's question:
"""


class ChatService:
    async def get_complete_response(self, question: str) -> dict:
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key,
            )

            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": f"{prompt_template}{question}"}],
                stream=False,
            )

            content = response.choices[0].message.content
            return {"status": "completed", "chunk": content}

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"status": "error", "message": str(e)}
            )
