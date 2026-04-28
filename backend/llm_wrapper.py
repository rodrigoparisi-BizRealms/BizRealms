"""LLM Wrapper - Works with emergentintegrations (Emergent) or OpenAI SDK (Railway/Production)"""
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

async def chat_completion(system_message: str, user_message: str, model: str = "gpt-4.1-mini") -> str:
    """
    Universal chat completion that works in both environments.
    - Emergent: uses emergentintegrations with EMERGENT_LLM_KEY
    - Production: uses OpenAI SDK with OPENAI_API_KEY or EMERGENT_LLM_KEY
    """
    # Try emergentintegrations first (Emergent environment)
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        llm_key = os.getenv('EMERGENT_LLM_KEY')
        if llm_key:
            chat = LlmChat(
                api_key=llm_key,
                session_id="bizrealms-coach",
                system_message=system_message,
            )
            chat.with_model("openai", model)
            response = await chat.send_message(UserMessage(text=user_message))
            return response
    except ImportError:
        logger.info("emergentintegrations not available, trying OpenAI SDK")
    except Exception as e:
        logger.warning(f"emergentintegrations failed: {e}")

    # Fallback to OpenAI SDK (Production/Railway)
    try:
        from openai import AsyncOpenAI
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('EMERGENT_LLM_KEY')
        if api_key:
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.9,
                max_tokens=1500,
            )
            return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"OpenAI SDK failed: {e}")

    # If both fail, return None (caller handles fallback)
    return None
