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

## 優選策略分頁與每日更新

`#champion` 是P19_support30的獨立模型續跑帳戶，使用 `../race-five-stock-lab/champion_latest.json` 指向的可追溯版本。進出指令、目前持倉、歷史決策／成交分開顯示；歷史基準仍固定截至2026-09-18。其他舊策略的資料日期不因本分頁更新而改寫。

本機排程 `100Q8 Champion Daily` 每日19:15讀取stock1下載的官方檔案，重建新日快取、重播固定規則、匯出並加密資料、提交推送main。失敗每30分鐘重試3次，日誌位於不納入Git的 `.local/daily-*.log`。需電腦開機、user登入、有網路及上游資料下載成功；它不直接連接券商下單。

手動重跑：`powershell -NoProfile -File scripts/daily_update.ps1`。密碼以Windows使用者DPAPI存於 `.local/publish-secret.xml`，不進Git。資料未變不重複提交；推送失敗會保留本地提交供重試。上游缺失日期會阻擋重播；網站資料日期落後時提示暫停新委託。

手機驗證涵蓋360、390、768、1440像素；逐日日期／方向篩選、卡片展開、分頁切換、頁面寬度及JS錯誤。瀏覽器檢查腳本為 `scripts/check_mobile.cjs`，需可用Playwright與Edge。
