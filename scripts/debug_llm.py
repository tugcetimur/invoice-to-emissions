import sys

from ollama import chat

from src.extract_llm import MODEL, SYSTEM_PROMPT, LLMInvoice
from src.extract_rules import read_pdf_text

text = read_pdf_text(sys.argv[1])
print(text)
print("-----")
response = chat(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Invoice text:\n\n{text}"},
    ],
    format=LLMInvoice.model_json_schema(),
    options={"temperature": 0},
)
print(response.message.content)
