
from google import genai

client = genai.Client(api_key="AIzaSyBJj8Fuvj-TczD_aSUPuvCFqm0vlBL9yU4")


def rewrite_query(message,liste):
        
    model_name = "gemini-2.0-flash"

    system_instruction = (
        f"Follows is the conversation history {liste}"
        f" + new user request {message}. "
        "If this is a follow-up question, rewrite ONLY the USER QUESTION with full context "
        "for semantic search purposes. If not, keep it as is. "
        "Return only the rewritten user query, nothing else."
    )

    response = client.models.generate_content(
        model=model_name,
        contents=[
            {
                "role": "user",
                "parts": [
                    
                       {"text": message}
                    
                ]
            }
        ],
        config={
            "system_instruction": system_instruction,
            "temperature": 0.2,
        }
    )

    print(response.text)
    return response.text

