import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_together import ChatTogether

load_dotenv()

ACTIVE_MODEL = "llama"  # change as needed

def get_llm():
    if ACTIVE_MODEL == "openai":
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    elif ACTIVE_MODEL == "claude":
        return ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.3,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    elif ACTIVE_MODEL == "mistral":
        return ChatTogether(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            temperature=0.1,
            max_tokens=1800, 
            together_api_key=os.getenv("TOGETHER_API_KEY")
        )
    elif ACTIVE_MODEL == "llama":
        return ChatTogether(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            temperature=0.1,
            max_tokens=2000,
            together_api_key=os.getenv("TOGETHER_API_KEY")
        )
    else:
        raise ValueError("Invalid ACTIVE_MODEL")

