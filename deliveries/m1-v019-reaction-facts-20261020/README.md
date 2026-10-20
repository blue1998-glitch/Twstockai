# M1 多參照反應事實附層 0.1

新增獨立純數值附層，不改原主圖、核心、參數、策略、資料庫、歷史或舊schema。原真實圖仍為固定成品fff47915523fab8c8de8279de8bbb7a26b05647b；本包是完整精度JSON，不是另一份HTML或自動選關。

- [下載資料小ZIP](M1_v019_reaction_facts_v01.zip)：965,955 bytes；6成員含原完整comparison-data、實際後來明示selection、新reaction-facts、來源收據、README及SHA。
- ZIP SHA256：`a18150ff8d548cb0456a2df446711a472e31f93abf06bfd663238a28f0ba546e`；[SHA檔](SHA256SUMS.txt)、[CRC與成員SHA](PACKAGE_VERIFICATION.json)。
- [直接讀新JSON](../../股票系統M1_v0_18/reaction_facts/generated/reaction-facts.json)、[明示來源例檔](../../股票系統M1_v0_18/reaction_facts/examples/selection.json)。
- [source、schema與CLI重現](../../股票系統M1_v0_18/reaction_facts/README.md)、[本輪實測與失敗](../../股票系統M1_v0_18/reaction_facts/validation_20261020/驗收報告.md)、[完整可貼Work指令](WORK_HANDOFF.md)。
- [沿用真實互動圖入口](../m1-v019-cross-scale-real-20261020/README.md)：下載原HTML看圖，本次沒有改圖或重開樣式驗收。

1,213筆原真實日K／量／MACD，2021-10-18～2026-10-16；本包固定1101／Raw／10/16收27.30，非即時。四個參照是既有B77研究低界、5/14原高、B88研究高界及10/14原高的**後來明示查詢**；並非新增挑關算法。實際selected_at見selection，historical_selection_time未核、historical_signal_eligible=false。

每參照close／high／low各有三態與精確差值，全部位置保存在records，49筆分欄位轉換／分段索引在transitions（**不是49個獨立型態、突破或交易訊號**）。實體方向與較前收方向分開；相鄰高低／Raw區間幾何、前一保存量分母／日期與50位描述比、原完整MACD分列。所有越過／跌回／相等保留，不以正MACD抹去收盤反證。

本輪22項Python契約測試PASS；新CLI／JSON重現與竄改拒絕、打包CRC／6成員抽出bytes均實測。原固定診斷ZIP再核CRC／SHA，原完整bars／MACD／SMA／source／basis／core／manual audit逐值全等；原2,155追蹤檔在交接更新前全未變，後來只在3份根交接前加最新節。未重跑舊7／47、35／60或任何無關套件，沒有UI變更／新瀏覽器測試／Android驗收。GitHub逐檔回讀收據另存後續文件提交，不自我宣稱收據已被自身雜湊涵蓋。

失敗保留：例檔準備初次按「同價＋同確認日」查詢得到各2個來源，唯一性斷言停止；未寫selection，依賴步驟隨後FileNotFoundError。診斷後改用既有B77／B88明示圖層原ID，不調核心、不任意同價合併。這是交付fixture準備失敗，不冒稱市場資料或原引擎事故。

未知保持：primary_pressure_id=null，整體解除／有效突破null；正式區界、量口徑增量／權重、強度衰減／重要性、合併／直接承接、生命階段、主壓力辨識用途仍未定。Raw公司行動、五年Adjusted、歷史公布可得、九待核日期／非窮盡日曆、Darvas正文及SQLite根因未核。來源待核缺日只保守分段，不補假K；日OHLC不證日內回測或先後。核心NOT_ESTABLISHED、分類NOT_VALIDATED、行動NOT_EVALUATED；Android **NOT_TESTED_NEW_BUILD**，file://不重試不繞過。

下一步 **Work** 用原互動圖配合新事實JSON研究整體壓力關係，不能把局部算術層完成當主壓力辨識或交易價值認可。未知策略取得明確裁決或有可重現缺陷才回Codex。不改main、不部署付費交易訊息子代理；換模式附最新已核SHA及完整續接。
