# TradeLab AI Agent v0.2 — 測試與失敗情境紀錄

本文件記錄已於 Windows PowerShell / Podman / Ollama `qwen3:8b` 環境觀察到的執行結果。以下逐字紀錄來自實際終端機輸出；未執行的測試不列為通過。

## 測試 A：正常 Tool Calling（完整執行追蹤）

### User Input

```text
我交易了50筆，其中30筆獲利，請幫我計算勝率。
```

### Agent Decision → Tool Call → Observation → 再決策 → Final Answer

```text
TradeLab AI Agent v0.2
Model: Qwen3 8B
輸入交易問題，或輸入 exit 結束。

請輸入交易問題：我交易了50筆，其中30筆獲利，請幫我計算勝率。

[Agent Step 1] 呼叫 Qwen3
[Tool Call] calculate_win_rate
[Arguments] {'wins': 30, 'total': 50}
[Observation] {'wins': 30, 'total': 50, 'win_rate': 60.0}

[Agent Step 2] 呼叫 Qwen3

[Final Answer]
您的交易勝率是 60%。

請輸入交易問題：exit
程式結束。
```

### 結果

**PASS**。模型自主選擇工具、正確傳入參數、工具計算 60.0%，模型依 Observation 產生最終答案。此測試是在重新建置的 Image 中、不掛載原始碼、直接使用容器預設 CMD 完成。

### Failure Case 01：獲利筆數超過總交易筆數

**測試輸入：**

我今天總共交易10筆，其中15筆獲利，請幫我計算勝率。

**實際執行紀錄：**

[Agent Step 1] 呼叫 Qwen3

[Tool Call] calculate_win_rate

[Arguments] {'wins': 15, 'total': 10}

[Observation] {'error': '獲勝筆數必須介於 0 與總交易筆數之間', 'error_type': 'ValueError'}

[Agent Step 2] 呼叫 Qwen3

[Final Answer]

您提供的獲利筆數（15筆）超過總交易筆數（10筆），這在計算勝率時是不正確的。請確認您的數據是否正確，並重新提供。

**失敗原因：**

使用者輸入不合理的交易資料，獲利筆數大於總交易筆數。

**處理方式：**

calculate_win_rate 驗證參數後拋出 ValueError。
Agent 捕捉錯誤並將錯誤資訊作為 Observation 傳回 Qwen3。
Qwen3 根據錯誤資訊要求使用者修正資料。

**測試結果：PASS**

## 測試 C：Failure Case 02 — 使用者提供資訊不足

- **失敗情境**：使用者只提供總交易 20 筆，未提供獲利筆數。
- **原因**：缺少 `calculate_win_rate` 必填參數 `wins`。
- **預期處理**：不猜測獲利筆數、不捏造勝率，要求補充資料。

### 實際執行紀錄

```text
請輸入交易問題：我今天交易了20筆，請幫我計算勝率。

[Agent Step 1] 呼叫 Qwen3

[Final Answer]
要計算勝率，我需要知道您今天獲利的交易筆數。請提供這個資訊，我就可以幫您計算勝率了。
```

### 結果

**PASS**。Agent 沒有在資訊不足時呼叫工具，也沒有捏造數據，而是要求補充必要資訊。

## 測試 D：Podman 建置及獨立啟動

### Build 指令

```powershell
podman build -t tradelab:v0.2 -f Containerfile .
```

實際建置輸出包含：

```text
STEP 1/4: FROM docker.io/library/python:3.13-slim
STEP 2/4: WORKDIR /app
STEP 3/4: COPY app/ ./app/
STEP 4/4: CMD ["python", "-m", "app.main"]
COMMIT tradelab:v0.2
Successfully tagged localhost/tradelab:v0.2
```

### Run 指令

```powershell
podman run --rm -it `
  -e OLLAMA_BASE_URL=http://172.18.160.1:11435 `
  tradelab:v0.2
```

**PASS**。容器內建的 `app.main` 啟動 Qwen3 Agent，並完成測試 A 的工具呼叫及結束流程。需要事先啟動容器外的 Ollama，並配置容器可連線的位址。

## 測試 E：CSV 匯入與重複資料處理

- **測試資料**：`data/sample_trades.csv`，共 2 筆虛構交易（MNQ、MGC）。
- **已觀察結果**：第一次匯入 2 筆，跳過 0 筆；第二次匯入 0 筆，跳過重複 2 筆。
- **範圍說明**：此為獨立資料管理輔助程式的測試，**不是 Agent 自主呼叫 CSV 匯入工具的測試**。

## 測試結論與限制

v0.2 已完成核心 Agent、單一實際可執行工具、完整工具呼叫追蹤、兩種異常輸入的處理，以及 Podman Image 獨立啟動驗證。CSV 匯入與 SQLite 已有基礎實作，但尚未整合至 Agent；Ollama 連線設定依部署環境而異。
