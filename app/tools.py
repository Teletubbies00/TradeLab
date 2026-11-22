def calculate_win_rate(wins: int, total: int) -> dict:
    if isinstance(wins, bool) or isinstance(total, bool):
        raise ValueError("交易筆數必須是整數")

    if not isinstance(wins, int) or not isinstance(total, int):
        raise ValueError("交易筆數必須是整數")

    if total <= 0:
        raise ValueError("總交易筆數必須大於 0")

    if wins < 0 or wins > total:
        raise ValueError("獲勝筆數必須介於 0 與總交易筆數之間")

    return {
        "wins": wins,
        "total": total,
        "win_rate": round(wins / total * 100, 2)
    }
