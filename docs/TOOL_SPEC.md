# TradeLab v0.2 — Tool 定義與錯誤處理

## 1. Agent 使用的工具

| 項目 | 說明 |
|---|---|
| 名稱 | `calculate_win_rate` |
| 實作位置 | `app/tools.py` |
| 呼叫位置 | `app/agent.py` 的 `execute_tool()` |
| 用途 | 依獲利交易筆數及總交易筆數計算勝率 |
| 輸入 | `wins: int`（獲利筆數）、`total: int`（總交易筆數） |
| 輸出 | `{"wins": 整數, "total": 整數, "win_rate": 百分比數值}` |
| 計算 | `round(wins / total * 100, 2)` |

### 有效輸入範例

```json
{"wins": 30, "total": 50}
```

### 輸出範例

```json
{"wins": 30, "total": 50, "win_rate": 60.0}
```

### 參數驗證與錯誤處理

- `wins` 或 `total` 是布林值或非整數：`ValueError("交易筆數必須是整數")`。
- `total <= 0`：`ValueError("總交易筆數必須大於 0")`。
- `wins < 0` 或 `wins > total`：`ValueError("獲勝筆數必須介於 0 與總交易筆數之間")`。
- Agent 的 `execute_tool()` 收到未知工具名稱：拋出 `ValueError`。
- Agent 捕捉工具執行時的 `ValueError`、`TypeError`、`KeyError`，包裝為 `{"error": "...", "error_type": "..."}` 的 Observation，讓模型根據錯誤回覆使用者。
- 若使用者未提供足夠資料，模型可不呼叫工具，直接要求補充資訊；此行為已在實際測試中觀察到。

## 2. Agent 工作流程

1. `app/main.py` 接收使用者輸入，呼叫 `run_agent()`。
2. `run_agent()` 建立 system/user 訊息，透過 `call_ollama()` 呼叫 Ollama `/api/chat`。
3. 模型決定是否提出 `tool_calls`。
4. 若提出工具呼叫，Agent 解析參數並執行 `calculate_win_rate()`。
5. 工具結果或錯誤成為 `role=tool` 的 Observation。
6. Agent 再次呼叫模型，取得最終自然語言回答。
7. 若模型沒有呼叫工具，直接輸出回答。

`stream` 與 `think` 均設為 `false`，最大迴圈輪數為 5。這是以 LLM Tool Calling 與 Observation 回饋實作的簡化 ReAct 式循環，並非完整的通用規劃系統。

## 3. 其他已實作功能（尚未接入 Agent Tool Calling）

### SQLite 資料庫初始化

- 檔案：`app/database.py`
- 函式：`initialize_database()`
- 目的：建立 `trades` 資料表。
- 資料庫路徑：環境變數 `TRADELAB_DB_PATH`，預設 `data/tradelab.db`。

### CSV 匯入

- 檔案：`app/import_trades.py`
- 函式：`import_csv(csv_path)`
- 輸入：CSV 檔案路徑。
- 輸出：`total_rows`、`inserted`、`skipped_duplicates`。
- 驗證：必要欄位、交易方向、日期時間順序、數量、價格、有效數值。
- 重複處理：對標準化交易欄位計算 SHA-256 指紋，略過相同資料。
- 錯誤處理：找不到檔案、CSV 格式錯誤、資料不合法或 SQLite 錯誤時顯示訊息並以非零狀態結束。

**重要**：這兩項目前是獨立 Python 程式，不是 Qwen3 可自主選擇的工具；不得在作業展示中宣稱 Agent 已能自動匯入 CSV 或查詢資料庫。
