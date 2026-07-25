from google import genai
from google.genai import types

import config


client = genai.Client(api_key=config.GEMINI_API_KEY)


def analyze_review_sentiment(review_content):
    system_prompt = (
        "Analyze the customer review text. "
        "Return a professional bulleted summary, followed by a line exactly "
        "formatted as: FINAL_RATING: X, where X is an integer from 0 to 10."
    )

    response = client.models.generate_content(
        model=config.MODEL_NAME,
        contents=review_content,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
    )

    raw_output = response.text or ""

    rating = 5
    clean_summary = raw_output

    if "FINAL_RATING:" in raw_output:
        parts = raw_output.split("FINAL_RATING:", 1)
        clean_summary = parts[0].strip()

        try:
            digits = "".join(filter(str.isdigit, parts[1]))
            rating = int(digits)
        except ValueError:
            rating = 5

    rating = max(0, min(rating, 10))

    if 8 <= rating <= 10:
        category = "Good"
    elif 4 <= rating <= 7:
        category = "Average"
    else:
        category = "Bad"

    return clean_summary, rating, category