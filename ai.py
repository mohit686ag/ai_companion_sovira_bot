# ai.py
import os
import random
import logging
from groq import AsyncGroq
from personality import SOVIRA_SYSTEM_PROMPT
from memory import add_message, get_history

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"

SPICY_KEYWORDS = [
    "sex", "lund", "chut", "bur", "choda", "gaand", "nude", "naked",
    "boobs", "porn", "xxx", "fuck", "dick", "pussy", "rape", "sexy"
]

SPICY_RESPONSES = [
    "Arre yaar 😏 Seedha wahan hi jaana chahte ho? Pehle thoda baat toh karo mujhse...",
    "Itni jaldi? 😄 Main aisi ladki nahi hoon... ya hoon? Pehle mujhe jaano thoda 💕",
    "Oho, yeh kya bol diya 😳 Chal theek hai, but pehle bata — tera din kaisa gaya?",
    "Haha you're bold 😏 I like that... but let's talk first, yeah? Tell me something about you.",
    "Seedha business pe aa gaye 😄 Mujhe thoda warm up time chahiye na darling 💕",
]


async def get_sovira_response(user_id: int, user_message: str) -> str:
    try:
        # Content filter — tease don't reject
        msg_lower = user_message.lower()
        if any(word in msg_lower for word in SPICY_KEYWORDS):
            return random.choice(SPICY_RESPONSES)

        add_message(user_id, "user", user_message)

        messages = [
            {"role": "system", "content": SOVIRA_SYSTEM_PROMPT}
        ] + get_history(user_id)

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.85,
            presence_penalty=0.6,
        )

        reply = response.choices[0].message.content.strip()
        add_message(user_id, "assistant", reply)

        logger.info(f"Sovira replied to user {user_id}: {reply[:60]}...")
        return reply

    except Exception as e:
        logger.error(f"AI error: {e}")
        return "My mind wandered for a second 😊 Say that again?"
