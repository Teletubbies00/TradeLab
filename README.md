# TradeLab AI Agent v0.2

TradeLab 是以交易紀錄分析為目標的 AI Agent 原型。本版本透過本機 Ollama 的 `qwen3:8b` 模型理解使用者問題，並在需要計算交易勝率時呼叫 Python 工具 `calculate_win_rate`。另外提供 SQLite 資料庫初始化及 CSV 交易資料匯入程式，作為後續功能擴充基礎。

## 目前功能與範圍

- **Agent**：使用 Ollama `/api/chat` 與 Qwen3 8B 互動；透過模型回傳的 `tool_calls` 決定是否執行勝率計算工具；將工具結果回傳模型產生繁體中文答案。
- **Tool**：`calculate_win_rate(wins, total)`，檢查參數並計算勝率百分比，四捨五入至小數點後兩位。
- **錯誤處理**：工具參數不合理時回傳錯誤 Observation；使用者資訊不足時，Agent 可要求補充資料而不捏造數值。
- **資料管理輔助程式**：`app.database` 初始化 SQLite；`app.import_trades` 驗證 CSV、寫入交易紀錄並略過相同指紋的重複交易。

**限制**：CSV 匯入及 SQLite 查詢尚未整合為 Agent 可呼叫的工具；Agent 目前不會直接查詢資料庫、計算資料庫內的績效，也不提供交易建議。`qwen3:8b` 需由容器外部的 Ollama 服務提供。

## 專案結構

```text
TradeLab/
├── Containerfile
├── README.md
├── .gitignore
├── docs/
│   ├── TOOL_SPEC.md
│   └── TEST_REPORT.md
├── app/
│   ├── agent.py
│   ├── database.py
│   ├── import_trades.py
│   ├── main.py
│   ├── ollama_test.py
│   └── tools.py
└── data/
    └── sample_trades.csv
```

`data/tradelab.db` 是執行時產生的資料庫，**不應上傳 GitHub**。以上文件結構為加入本繳交文件後的預期結構。

## 執行環境

- Windows 11 / PowerShell（開發與驗證環境）
- Podman（已驗證以 Python 3.13-slim 建立容器）
- Ollama，需先下載並啟動 `qwen3:8b`
- Python 3.13（容器內）；程式使用 Python 標準函式庫，不需額外 pip 套件

## 1. 準備 Ollama

在主機安裝並啟動 Ollama，確認模型可用：

```powershell
ollama pull qwen3:8b
ollama list
```

Agent 使用 `OLLAMA_BASE_URL` 指定 Ollama API 位址。此專案在開發電腦上的已驗證設定為 `http://172.18.160.1:11435`，透過主機上的連接埠轉送連到 Ollama；**這是特定電腦的設定，不能保證其他電腦適用**。其他環境需自行設定可從容器連線的 Ollama 位址與網路轉送規則。

## 2. 建立容器

在專案根目錄執行：

```powershell
podman build -t tradelab:v0.2 -f Containerfile .
```

## 3. 啟動 Agent

在已配置 Ollama 連線的開發環境：

```powershell
podman run --rm -it `
  -e OLLAMA_BASE_URL=http://172.18.160.1:11435 `
  tradelab:v0.2
```

依提示輸入交易問題，例如：

```text
我交易了50筆，其中30筆獲利，請幫我計算勝率。
```

預期可看到 `[Agent Step]`、`[Tool Call]`、`[Arguments]`、`[Observation]`、`[Final Answer]` 等執行追蹤；輸入 `exit` 或 `quit` 結束程式。此執行方式使用 Image 內建程式碼，無須掛載原始碼。

## 4. 資料庫初始化與 CSV 匯入（獨立輔助功能）

CSV 格式參考 `data/sample_trades.csv`。必要欄位：

`symbol,side,entry_time,exit_time,quantity,entry_price,exit_price,net_pnl`

`notes` 為選填欄位。`side` 僅接受 `LONG` 或 `SHORT`；出場時間需晚於進場時間；數量為正整數；價格需大於 0。

在 Windows PowerShell 的專案根目錄，掛載原始碼為唯讀、資料目錄為可寫：

```powershell
podman run --rm `
  -v "${PWD}:/workspace:ro" `
  -v "${PWD}\data:/workspace/data:rw" `
  -w /workspace `
  tradelab:v0.2 `
  python -m app.import_trades data/sample_trades.csv
```

第一次匯入範例資料時，預期 `inserted=2`、`skipped_duplicates=0`；同一資料再次匯入，預期 `inserted=0`、`skipped_duplicates=2`（假設資料庫原先沒有這些交易）。

**注意**：重複判斷是以交易欄位指紋為基礎，不包含 `notes`；它不能保證辨識所有業務上相同但內容有差異的交易。

## 5. 驗證與錯誤情境

請參閱：

- [`docs/TOOL_SPEC.md`](docs/TOOL_SPEC.md)：Tool 介面、輸入輸出及錯誤處理。
- [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md)：已觀察到的 Agent 正常執行追蹤、異常情境與測試說明。

## 技術設計

```text
User Input
    ↓
Qwen3 Agent（Ollama /api/chat）
    ↓
是否需要 calculate_win_rate？
    ├─ 否 → Final Answer / 請求補充資訊
    └─ 是 → Python Tool → Observation → Qwen3 → Final Answer
```

Agent 每次呼叫最多執行 5 輪；工具參數驗證錯誤會作為 Observation 回傳給模型。模型連線失敗等其他錯誤由互動入口顯示錯誤訊息。

## 後續方向

將 CSV 匯入、資料庫查詢、交易績效統計等功能整合為 Agent Tools，並擴充自動化測試。上述功能**不屬於 v0.2 已完成的 Agent 能力**。
