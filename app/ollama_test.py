import json
import os
import urllib.request

OLLAMA_URL = os.environ.get(
    "OLLAMA_BASE_URL",
    "http://172.18.160.1:11435"
)

payload = {
    "model": "qwen3:8b",
    "messages": [
        {
            "role": "user",
            "content": "請用繁體中文簡單說明什麼是交易勝率。"
        }
    ],
    "stream": False,
    "think": False
}

request = urllib.request.Request(
    url=f"{OLLAMA_URL}/api/chat",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("正在連接 Qwen3 8B...")

try:
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)

    print("\nQwen3 回答：")
    print(result["message"]["content"])

except Exception as error:
    print(f"連線或推理失敗：{error}")
    raise
