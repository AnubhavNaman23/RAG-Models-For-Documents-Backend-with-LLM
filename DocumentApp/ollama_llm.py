import ollama

LLM_MODEL = "phi3:mini"

def generate_response(context, question):
    prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    response = ollama.generate(model=LLM_MODEL, prompt=prompt)
    if hasattr(response, "response"):
        return response.response
    if isinstance(response, dict) and "response" in response:
        return response["response"]
    return str(response)
