import json
import os
import urllib.request
import urllib.error

from app.tools import calculate_win_rate


OLLAMA_URL = os.environ.get(
    "OLLAMA_BASE_URL",
    "http://172.18.160.1:11435"
)

MODEL = "qwen3:8b"


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_win_rate",
            "description": "計算交易勝率。當使用者提供獲利筆數與總交易筆數時使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "wins": {
                        "type": "integer",
                        "description": "獲利交易筆數"
                    },
                    "total": {
                        "type": "integer",
                        "description": "總交易筆數"
                    }
                },
                "required": ["wins", "total"]
            }
        }
    }
]


def call_ollama(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "stream": False,
        "think": False
    }

    request = urllib.request.Request(
        url=f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def execute_tool(name, arguments):
    if name == "calculate_win_rate":
        return calculate_win_rate(
            wins=arguments["wins"],
            total=arguments["total"]
        )

    raise ValueError(f"未知工具：{name}")


def run_agent(user_input):
    messages = [
        {
            "role": "system",
            "content": (
                "你是 TradeLab AI Agent，使用繁體中文回答。"
                "涉及交易勝率計算時，必須使用提供的工具。"
                "不得捏造交易資料或計算結果。"
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    for step in range(5):
        print(f"\n[Agent Step {step + 1}] 呼叫 Qwen3")

        result = call_ollama(messages)
        message = result["message"]

        messages.append(message)

        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            answer = message.get("content", "")
            print(f"\n[Final Answer]\n{answer}")
            return answer

        for tool_call in tool_calls:
            function = tool_call["function"]
            name = function["name"]
            arguments = function.get("arguments", {})

            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            print(f"[Tool Call] {name}")
            print(f"[Arguments] {arguments}")

            try:
                observation = execute_tool(name, arguments)
            except (ValueError, TypeError, KeyError) as error:
                observation = {
                    "error": str(error),
                    "error_type": type(error).__name__
                }

            print(f"[Observation] {observation}")

            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": json.dumps(observation, ensure_ascii=False)
            })

    raise RuntimeError("Agent 超過最大執行步數")


if __name__ == "__main__":
    question = input("請輸入交易問題：")
    run_agent(question)
