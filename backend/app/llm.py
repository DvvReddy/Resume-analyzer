import os
from transformers import pipeline


MODEL_ID = os.getenv("MODEL_ID", "distilgpt2")

_gen = None


def get_generator():
    global _gen
    if _gen is None:
        _gen = pipeline("text-generation", model=MODEL_ID)
    return _gen


def generate_text(prompt: str, max_new_tokens: int = 220) -> str:
    gen = get_generator()
    out = gen(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
    )
    return out[0]["generated_text"]
