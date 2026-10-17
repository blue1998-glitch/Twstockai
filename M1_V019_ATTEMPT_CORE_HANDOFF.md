# 接續建構：嘗試關卡與量先價核心已可整合

本輪基於 `dev/m1-v018-chart-annotations` 原頭 `99d41200b2207b654f080e497804e5b94edfc3e3`，新增獨立 `attempt-evidence-candidate/0.1`。使用本文件所在分支的最新提交，**不要從 main、54a3ea3 或舊 ZIP 覆蓋本次新增程式**。原 v0.19 網頁成品與歷史引擎／庫保留。

## 先讀

1. 根目錄 AGENTS.md、PROJECT_VISION.md、CONTINUE_IN_WORK_MODE.md 最上方。
2. M1_V019_VISUAL_RULE_NOTES.md 最新 21:39 核心裁決。
3. `股票系統M1_v0_18/product_candidate/ATTEMPT_EVIDENCE.md`。
4. `股票系統M1_v0_18/product_candidate/validation_attempts_20261017/驗收報告.md`、report.json、synthetic_example_output.json。

## 本輪完成的是什麼

純核心 API `product_candidate.attempt_evidence.evaluate(payload)`，不依賴網頁、Streamlit、SQLite 或 API。

已選日線背景中，101 與左區上緣 106 是不同嘗試關卡；量超越指定左區來源日的最高量、而價格尚未越上緣，保存量先價支持證據。沒有量先價不否認 101；放量不等於過 106，後來價格是否實際越過另記。未來跌回追加事實，不抹去過去。

價格子條件 MET 與整體交易資格 NOT_EVALUATED 分開。使用者認為量先價提高成功機率，但沒有實測勝率數字；趨勢延續可成強勢股仍需正式分類條件，不自行訂幾根 K、幾日或幾％。

## 可直接執行的下一段工程

不需再問使用者是否理解 101／106 或是否允許一般整合。將此核心作為**獨立、明確啟用的候選證據來源**接入圖形／重播流程，先用已保存工程例檢查：

- 顯示日線背景、手動明選近期高點與左區來源的狀態，不把工程例稱真實股票，不把來源未選完的資料送去自動選股。
- 僅渲染核心輸出的兩個嘗試條件、當時量／左區最高量、量先價或順序未知、後續價格進展及跌回事件；瀏覽器不重算分析。
- 逐時點顯示當時可知的 K／量與事件，不將 09:30 量或次日 106 回填到 09:10。盤中與完成日分開，完整／片段歷史覆蓋明示。
- 支持、反證、缺證與目前持倉分開。尚未接持倉時不要把假設進場當真實成交，也不要從不宜新買推出自動賣出。
- 下載保存完整輸入來源、基底、參照、規則版本、frame／event ID、未知及原精度；普通畫面價格可兩位小數，計算不可截斷。
- 新產物使用獨立來源／檔名與版本，既有候選資料、HTML、schema、SQLite 和原策略不覆寫。不因新規則改寫舊兩日失效資料。
- 先做有意義的 prefix／事件一致性及下載核對；有實際瀏覽器再記真實瀏覽器結果，Android 另外由使用者實機驗收，不能借用舊報告。

真實資料接入前：近期高點／左區來源仍須明選或由另行認可的選取規則產生，確認同股票／來源／Raw或Adjusted基底與錨定、公司行動及當時可得資料。沒有實際盤中序列時只顯示已完成日線證據與「盤中資料缺少」，不由日 OHLC 編造。

## 不在本輪擅自決定的核心

自動左區辨識與重要性、正式三種整理／生命階段、強勢延續的數值判別、持倉處置、資金與換股優先權、實證勝率。若需要改這些，用實際保存案例或清楚圖形問真正核心差異，不開大量閾值問卷。

1101／2884 原保存案例仍需核心覆核；未完成項目不可因這個小核心通過而勾完成。全市場圖形選股、動能換股與資金閉環三大目標仍未完成。

## 已執行與待驗收

- 新核心：24 項 unittest 通過。
- 既有候選回歸：16 項通過；本輪共 40 項不同測試，不與舊 286 相加。
- CLI：輸出 7 frame／12 事件，讀回與 API 相同；全為假想工程例。
- 候選 UI 整合、實際瀏覽器、Android、新規則真實分類／績效：未完成／未測。
- SQLite 原事故根因仍未知。

## 重現命令

先在 repository root 執行 `python3 codex/bootstrap_m1.py --hydrate-missing`，保留任何既有差異；進入 `股票系統M1_v0_18`：

```bash
python3 -m unittest discover -s tests -p test_attempt_evidence.py -v
python3 -m unittest discover -s tests -p test_product_candidate.py -v
python3 -m product_candidate.attempt_evidence product_candidate/fixtures/attempt_evidence_v01.json
```

後續以 **Codex** 進行這段已明確的整合工程；真正未決策略仍回 Work Mode 用圖討論。成果直接更新原獨立分支並保留本交接，不改 main。
