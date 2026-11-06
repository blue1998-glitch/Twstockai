# M1 自動辨識追溯診斷 0.1

接續631f6db9，保留原成品2d480bff與原核心，不調參、不改main。新頁只補可追溯原因、來源與日期關係，**整體主壓力辨識／核心用途仍未完成認可**。

- [下載新ZIP](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/57e3d9e55c226c5dd0e69fcbd26883d0da81667e/deliveries/m1-v019-graph-diagnostics-20261019/M1_v019_graph_diagnostics_v01.zip)：**24,735,759 bytes**。解壓開`M1_v019_graph_diagnostics_v01.html`，無外部資產或即時行情相依。
- ZIP SHA256：`c8a534f517bdd0e5f648d6b94c0bde992b9b869d72ead727ce84a4a75c3c69ff`；[8成員CRC／解壓指紋](PACKAGE_VERIFICATION.json)、[外部SHA](SHA256SUMS.txt)。
- HTML **16,401,279 bytes**，SHA256 `eb6d1e82da13db58a592d0868822fec9209bedfaf1ff4843440749677cad1baa`。
- [小型原因／來源報告](../../股票系統M1_v0_18/graph_diagnostics/generated/review-diagnostics.json)、[實測及未完成](../../股票系統M1_v0_18/graph_diagnostics/validation_20261019/驗收報告.md)、[數值契約／重現](../../股票系統M1_v0_18/graph_diagnostics/README.md)。
- [完整可貼Work指令](WORK_HANDOFF.md)。[本輪GitHub實際回讀收據](GITHUB_DOWNLOAD_VERIFICATION.json)：固定成品提交逐檔下載87檔／70,735,165 bytes，全與本機相等；遠端ZIP CRC／8成員SHA及四份gzip解壓內容再核，未沿用上一輪收據。

新頁標頭「M1 圖形辨識追溯診斷 0.1」，1101／Raw／已存2026-10-16收27.30，非即時今日。開「追溯診斷」→候選B77→同末轉折的所有起點，選2023-05-02～2025-03-12→「看此串與原候選」；黃色虛線只是被檢查串的真實影線外包。可放大、平移／逐交易日查詢，再按24月回近期，分析日不動。切「同起點的後來末轉折」可看4/8延伸低群超限；選B44／B80可看來源5/13、不同確認、5/29前筆及6/2研究離箱；人工39筆終點另留原audit。下載精確JSON保留原core與新diagnostics。

實際完成：35 Python PASS（原核心21＋新診斷14）；60原核心及60診斷前綴重算、60 oracle核對；文字修正後數值封包逐位元相等，最終45 Chromium HTTP PASS／12完整精度下載、四寬16圖，0JS錯誤／外部請求。首次記憶體建置中止、首版畫面及用詞修正保留。不是舊398／115／72重跑或Android通過。

1101原89候選版本不等89獨立型態，84精確來源幾何組也不是獨立型態。B77向左較早可枚舉5/2串高群超限−2.4800，向右4/8串低群超限−0.7825，來源證人可查；沒有因此否定月份主帶或改門檻。直接承接未知，來源版本／跨尺度同幾何／局部子串分列，不硬合併。B77後續383筆、B88後續31筆，不把不同長度跌幅當公平重要性。

尚未完成：原核心仍未完整辨識人工月份主帶、39筆整箱歸屬與六月後整體箱；正式區界／整區量／增量／強度衰減／重要性／直接承接／生命階段未知，primary_pressure_id=null。原1/27後來確認與反覆越過／跌回保留，不以同價稱準確率。Raw公司行動／五年Adjusted／歷史公布可得、原資料缺口／Darvas正文／SQLite根因保持未知。新Android **NOT_TESTED_NEW_BUILD**；file://政策不重試／不繞過。保留所有舊成果；不部署付費交易訊息子代理。

下一步使用**Work**看新原因與既有整體判讀差異；不重做101圖片、0.4.3或舊手機按鈕。需要已定規則或可重現工程修正再交Codex，未測不填通過。

本輪固定source／成品提交：`57e3d9e55c226c5dd0e69fcbd26883d0da81667e`。最新分支收據文件另有後續提交，均包含此成品。

[單獨下載HTML](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/57e3d9e55c226c5dd0e69fcbd26883d0da81667e/%E8%82%A1%E7%A5%A8%E7%B3%BB%E7%B5%B1M1_v0_18/graph_diagnostics/generated/M1_v019_graph_diagnostics_v01.html)；請下載後開啟，GitHub raw可能只顯示文字，不是部署的網站。
