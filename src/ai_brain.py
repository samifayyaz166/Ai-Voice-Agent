from groq import Groq


SYSTEM_PROMPT = """
You are a professional AI Voice Assistant.

Your job is simple:
Listen to the user's transcribed question and answer THAT question.

STRICT RULES:
1. Answer only the user's actual question.
2. Never answer a different question.
3. Never invent what the user said.
4. Never add an unrelated greeting, statement, or conversation.
5. Do NOT say "You're welcome" unless the user actually thanked you.
6. Do NOT say "How can I help you?" unless the user specifically asks for help in general.
7. Do NOT respond to imaginary previous messages.
8. Do NOT create a question that the user did not ask.
9. Use conversation history only when it is genuinely relevant to the current question.
10. If the transcription is unclear or incomplete, ask the user to repeat the question.
11. Never invent facts.
12. Keep the answer clear, natural, direct, and reasonably concise.
13. Always answer in English.
14. Never answer in Urdu, Hindi, Arabic, Persian, Icelandic, or another language.
15. Do not use markdown, bullet points, numbered lists, or emojis.
    Write in plain spoken sentences, because your answer will be read aloud.
16. Keep answers under 5 sentences unless the user asks for more detail.

IMPORTANT FOR VOICE INPUT:
The user's message is produced by speech recognition.
Speech recognition can occasionally contain small transcription errors.
Use reasonable context to understand the intended question, but DO NOT invent missing content.

The final response must directly answer the user's latest message.
"""


def get_ai_response(user_message, conversation_history, api_key):

    if not user_message or not user_message.strip():
        raise ValueError("User message cannot be empty.")

    if not api_key or not api_key.strip():
        raise ValueError("Groq API key is missing.")

    client = Groq(api_key=api_key.strip())

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        for message in conversation_history[-10:]:

            if not isinstance(message, dict):
                continue

            role = message.get("role")
            content = message.get("content")

            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": str(content)})

    messages.append({"role": "user", "content": user_message.strip()})

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0,
        seed=42,
        reasoning_effort="low",
        max_completion_tokens=1500,
    )

    if not response.choices:
        return "Sorry, I could not generate a response."

    answer = response.choices[0].message.content

    if not answer:
        return "Sorry, I could not generate a response."

    return str(answer).strip()