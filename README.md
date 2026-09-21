# 100Q8

RACE興櫃五檔策略靜態追蹤站。GitHub Pages直接發布根目錄，不需要Node或後端服務。

## 更新資料

在本專案目錄執行：

```powershell
python scripts/export_dashboard.py --lab ..\race-five-stock-lab
```

輸出為`data/dashboard.json`。提交並推送`main`後，GitHub Actions會部署Pages。

網站明確區分歷史回測、歷史模型觀察持股與截止日後的紙上新訊號。不得將歷史模型持股當成新帳戶追價指令。
