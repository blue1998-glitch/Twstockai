# M1 公司行動與逐日資金帳 0.1

本輪獨立工程已實作與測試；**市場總淨報酬比較仍未完成：70窗口全拒算、2不足，合格0**。不以原P1-7價格報酬替代，不挑勝出比例。

[下載小ZIP（約0.50 MB）](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-actions-ledger-20261022/m1-actions-ledger-v01-20261022.zip) · [SHA256SUMS](SHA256SUMS) · [封包核對](bundle-receipt.json) · [GitHub固定提交與逐檔回讀](GITHUB_READBACK.md)

SHA256：`b31bb240bd47536ab03fb627da37f0ceaa0d33460328caa328d38428d3ac80b5`；498439 bytes，293 members，CRC及成員SHA全通過。

[事件表、逐日帳與完整實測入口](../../股票系統M1_v0_18/rotation_research/action_data_20261022/README.md) · [完整續接指令](../../股票系統M1_v0_18/rotation_research/action_data_20261022/WORK_HANDOFF.md)

新44項定向測試及122原件／舊輸入一致核對通過；小ZIP在新臨時目錄解壓後44項再次通過、研究重現成功，292個manifest成員於重現後仍逐位元相同。這是同44項驗證，不是88個獨立測試。證據：[PACKAGE_VALIDATION.json](PACKAGE_VALIDATION.json)、[封包測試log](package-tests.log)、[研究log](package-study.log)。

下載後解壓到新資料夾，先讀START_HERE.md。包內含新Python、精確JSON／CSV／契約／原件子集，可標準Python離線驗44項與資格核查；不是完整歷史專案，不覆蓋原專案。GitHub上也能直接讀Markdown／JSON／CSV，不需安裝或部署。

四現金＋一配股組件有來源；配股比／可交易日、完整減資／其他行動／2026/7/25～10/16覆蓋、淨分配／日曆／期初權利仍缺。一次官方PDF補查Tunnel403已存，無繞過；公布可得、Raw／Adjusted、主檔及SQLite未知不變。工程情境帳不是行情；真實毛額預定時程不是實際到款／淨現金。原core／策略／庫／歷史／舊頁／舊ZIP及main保持。

沒有新增UI或本輪瀏覽器／Android驗收，Android仍NOT_TESTED_NEW_BUILD，不需重做舊按鈕截圖。下一步用**Codex**補可追溯資料；切Work時貼完整WORK_HANDOFF，先讀最新分支與固定交付收據。未部署、付費、交易、發訊息或啟動子代理。
