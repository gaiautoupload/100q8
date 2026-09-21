# 100Q8

RACE興櫃五檔策略靜態追蹤站。GitHub Pages直接發布根目錄，不需要Node或後端服務。

## 更新資料

在本專案目錄執行：

```powershell
python scripts/export_dashboard.py --lab ..\race-five-stock-lab
$env:Q8_PASSWORDS='密碼一;密碼二'
node scripts/encrypt_dashboard.mjs
```

第一步在本機輸出不納入Git的`data/dashboard.json`；第二步產生可部署的AES-GCM加密檔`data/dashboard.secure.json`。提交並推送`main`後，GitHub Actions會部署Pages。密碼不可寫入repo。

網站明確區分歷史回測、歷史模型觀察持股與截止日後的紙上新訊號。不得將歷史模型持股當成新帳戶追價指令。
