# M1：1101人工三關新版下載

**新版：hurdle-chart-view/0.1**，請開`M1_v0_19_three_hurdles.html`，不要用舊`M1_v0_19_pressure_chart.html`代替本次驗收。預設1101、新官方Raw／2026-10-16／收27.30、24月486根。

- [直接下載新版小ZIP](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-three-hurdles-20261018/M1_v019_three_hurdles_page.zip)
- [ZIP的SHA256清單](SHA256SUMS.txt)及[CRC／解壓逐檔SHA報告](PACKAGE_VERIFICATION.json)
- [新版使用／精確綁定契約](../../股票系統M1_v0_18/hurdle_chart/README.md)
- [本輪實測與限制](../../股票系統M1_v0_18/hurdle_chart/validation_20261018/驗收報告.md)
- [新版Android驗收最上方](../../M1_V019_PRESSURE_CHART_ANDROID_ACCEPTANCE.md)
- [直接貼給Work的指令](WORK_HANDOFF.md)

ZIP解壓後開HTML；同包有原人工案例、簡短說明及內部SHA。HTML約35MiB，包含真實日K／指標，沒有連網載行情。ZIP大小及SHA以PACKAGE_VERIFICATION.json為準。這次只提供新版小ZIP；原五年主圖完整三包與所有舊頁保留在前一交付目錄，**舊完整包不包含新版三關**。工程source直接在同分支hurdle_chart/，Git checkout依root bootstrap補原資產。

原①26.10／④26.85收盤已過點價，後續人工G1 35.50、G2 40.25、G3 50.20分開。點卡片標題讀證據；點定位來源不改分析日，按24月返回近期24月。G3五日都可從表格定位，顯示錨不代表唯一使用者日期。超軸提示不強拉50.20壓扁近期K，只有精確source-frame-basis／10/16案例才套。

實測：365 Python PASS；真實Chromium **208 HTTP檢查PASS**，100 oracle下載及另2次人工層下載核對。報告整體 **PASS_WITH_BLOCKED_CHECK**：額外file://開檔受雲端管理政策阻擋；沒有繞過。新版Android **NOT_TESTED_NEW_BUILD**，不可沿用舊pressure部分驗收，手機載入／開檔／效能／用途須回Work提供新原圖、操作及原JSON。

Raw公司行動／五年Adjusted及歷史公布時刻未完整核實，五年高不認證全歷史高。區界／整區量／增量／強度／衰減／自動選關／生命階段未定，人工接入不是全市場核心辨識完成。TWSE六日Work補證未接入產品稽核、TPEX仍待；其他資料缺口與SQLite未證實根因保留。沒有改main、原引擎／策略／資料庫／歷史或舊頁。

GitHub保存與實際下載核對以同目錄GITHUB_DOWNLOAD_VERIFICATION.json的固定提交、位元組與SHA為準；沒有收據前不以此README代替遠端實測。
