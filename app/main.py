from app.agent import run_agent


def main():
    print("TradeLab AI Agent v0.2")
    print("Model: Qwen3 8B")
    print("輸入交易問題，或輸入 exit 結束。")

    while True:
        try:
            question = input("\n請輸入交易問題：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n程式結束。")
            break

        if question.lower() in ("exit", "quit"):
            print("程式結束。")
            break

        if not question:
            print("請輸入問題。")
            continue

        try:
            run_agent(question)
        except Exception as error:
            print(f"[Agent Error] {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
