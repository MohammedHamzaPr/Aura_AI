from ollama import chat

response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": "مرحبا، أنت الآن العقل المحلي لمشروع AURA. عرف نفسك."
        }
    ]
)

print(response.message.content)
