import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = BASE_DIR / "SYSTEM_PROMPT.txt"
USER_PROMPT_PATH = BASE_DIR / "USER_PROMPT.txt"


def get_openai_response(prompt: str) -> str:
    load_dotenv()

    api_key = os.environ.get("API_KEY")
    endpoint = os.environ.get("ENDPOINT")
    deployment_name = os.environ.get("DEPLOYMENT_NAME")

    client = OpenAI(base_url=endpoint, api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        return completion.choices[0].message.content

    except (KeyError, IndexError, TypeError):
        raise SystemExit(f"Unexpected prompt format: {prompt}")


def load_prompt(prompt_path: Path, system_prompt: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    return prompt_template.replace("{{CV}}", system_prompt)


SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
prompt = load_prompt(USER_PROMPT_PATH, SYSTEM_PROMPT)
response = get_openai_response(prompt)

print(response)
