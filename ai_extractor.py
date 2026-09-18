
import os
import json
import base64

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "qwen/qwen3.8-27b"


def extract_from_text(receipt_text):
    prompt = """
You are an expense receipt extraction system.

Extract the following fields from the receipt text:

- merchant
- amount
- expense_date
- category
- reason

Rules:
1. Return ONLY valid JSON.
2. amount must be a number.
3. expense_date must use YYYY-MM-DD.
4. category must be one of:
   Travel, Meals, Supplies, Accommodation, Communication, Other
5. If a field cannot be determined, use null.
6. Do not invent information.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": receipt_text
            }
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_completion_tokens=500
    )

    return json.loads(
        response.choices[0].message.content
    )


def extract_from_image(image_path):
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    prompt = """
Read this expense receipt and extract:

- merchant
- amount
- expense_date
- category
- reason

Rules:
1. Return ONLY valid JSON.
2. amount must be a number.
3. expense_date must use YYYY-MM-DD.
4. category must be one of:
   Travel, Meals, Supplies, Accommodation, Communication, Other
5. If a field cannot be determined, use null.
6. Do not invent information.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:image/jpeg;base64,"
                                f"{image_data}"
                            )
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_completion_tokens=500
    )

    return json.loads(
        response.choices[0].message.content
    )