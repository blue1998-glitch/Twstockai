# M1 v0.18：結構標記版交付

只想使用：下載 [單頁網頁 ZIP](M1_v0_18_annotations_page.zip?raw=true)，解壓後在裝置以瀏覽器開啟。也可直接儲存 [HTML](M1_v0_18_annotations.html?raw=true)。內含原保存資料，不必另外下載資料庫，也不連線新行情。

完整交接：下列三包各自包含部分檔案，全部下載並解壓到同一資料夾即可，不需要舊 ZIP。
- [M1_v0_18_annotations_01.zip](M1_v0_18_annotations_01.zip?raw=true)：19.02 MB
- [M1_v0_18_annotations_02.zip](M1_v0_18_annotations_02.zip?raw=true)：19.02 MB
- [M1_v0_18_annotations_03.zip](M1_v0_18_annotations_03.zip?raw=true)：19.02 MB

共 887 檔，CRC、SHA-256 及合併內容均已核對。驗收報告在解壓後 annotations/validation_20261017/驗收報告.md。

已實測：Python270項、bootstrap整合1項、相關Node46項；原手機版與標記版各72次真實Chromium下載核對。實體Android尚未測，原SQLite根因仍未知。

範例：TWSE / 1101 → Raw → 2026-09-30 → structure-0.3-research 日線版本 → 週月版本 → 讀取。可點日線轉折點／色帶，或用標記證據清單查看原記錄。沒有有效區域時不補造；Adjusted不生成還原日K。

Source直接保留在同分支 股票系統M1_v0_18/；全新Git checkout需先用 root 的 python3 codex/bootstrap_m1.py --hydrate-missing 補齊歷史資產，再依交接匯出頁面。直接下載的三個ZIP已含完整資產，無需bootstrap。

下一步用工作模式對話做新版Android實機驗收；實機若有程式問題再回Codex。
