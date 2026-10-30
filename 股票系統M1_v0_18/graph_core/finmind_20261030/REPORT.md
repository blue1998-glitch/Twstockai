# M2-3 實際交付與自審

## 新增能力

既有 `/workspace/Twstockai`、`dev/m1-v018-chart-annotations`，起始本地及遠端同為 `07fbbb034468aaa83de1df04743029bd54c5c691`，index／修改／新增皆空。未發現另一個活躍工程寫入程序；程序快照不能保證平台外沒有寫入者，保存前另核遠端。只此Codex，沒有代理、worktree或新分支。

原 `graph_core_chart.build.input_for` 接的是既有父圖層來源容器，不能直接接FinMind回應；不重建父圖、UI或儲存框架。本輪新 `finmind_adapter` 純轉欄位／驗證，直接委派原 `graph_core.core.analyze`。`finmind_run` 只做有限外部HTTP／本地IO與協調；既存TWSE月表欄位驗證重用 `src/source_audit.py::parse_twse_month`，不重寫圖形／會計／數值公式。

固定scope在CLI及純入口檢查：2884/TWSE、TaiwanStockPrice、2026-03-01～07-22；明示截點必在範圍內並精確供應。欄位open/max/min/close → open/high/low/close，Trading_Volume → volume_shares_scaled，原生股數不縮放。JSON浮點字面值用Decimal讀取，二進位float輸入拒絕。

## 真實資料實際結果

官方API本輪只查一次：成功取得98筆，完整回應只保存在 `/workspace/twstockai-local-data/m2-3-finmind-20261030/`。最後原source執行結果在 `/workspace/twstockai-local-data/m2-3-finmind-final-20261030/`；自審前結果另留 `/workspace/twstockai-local-data/m2-3-finmind-run-20261030/`，沒有覆寫。後兩次運算均重用同一回應，不重查。

| 驗收 | 實際結果 | 證據 |
|---|---|---|
| 2884有限資料、日期／OHLC／整數原股數 | 通過；同股官方已觀察日期相符，無補值 | 公開 `real-validation-summary.json`；完整檢查輸入／結果僅本地 |
| 07-21、07-22明示as_of | 原core實際執行，分別97／98筆 | 同上，兩個analysis狀態；本地input／result各兩份 |
| 兩日官方核對 | OHLC與原生股數逐欄皆相等 | official_two_day_field_matches；官方原件路徑及SHA見baseline.json |
| 未來隔離 | 07-21結果與截短／改寫07-22的完整核心結果逐值相等 | prefix_control；完整控制本地prefix-control.json |
| 2884 07-01不比價 | 既存月表X及圖例確認；原basis_break_dates接線中斷 | 摘要basis_break_dates，不推定事件類型 |
| 8069兩日精度 | 整數張數；精確股數UNKNOWN／拒認 | precision_8069；沒有重查或宣稱讀到Library內8069回應 |
| source完整性與數值前綴 | 全回應identity留provenance，數值結果只綁前綴；不以全檔SHA比較因果結果 | 純函式與前綴測試；完整身份本地 |

歷史available_at未證明，bar.available_at=null、外層historical_available_at=UNKNOWN；取得時間不回填到歷史。只接受台北日期已過去的日線，同日即使可能已收盤也保守拒絕。獨立既存同股月表只能證已觀察日期；不能認證完整交易所曆或兩來源同時遺漏，所以calendar_completeness仍UNKNOWN。

## 合成驗證與診斷

先保存CONTRACT、input／expected及原source指紋，再實作。全部新行情fixture為人造價量，不含FinMind真實列。27份拒絕輸入於首次個別執行前保存，actual見synthetic-actual.json，全部與預期一致；另有正例、未來／基底／時區／數值環境／input不變／純數值無IO／Git輸出拒絕／HTTP不重試等控制。

- `tests-first.log`：14個新方法，13 PASS／1 ERROR。反例檔生成命令因工作目錄多加一層導致檔案未產生；該方法因缺檔未實跑反例。原log原樣保存，未修改oracle。
- `tests-targeted-final.log`：補成反例檔後只執行該一方法及3個必要core回歸，4 PASS。
- 自審將純入口同樣限制在本輪日期範圍，並將外層run也放入獨立Decimal Context；`tests-self-review.log`只重跑受影響的file-run方法與一個新scope方法，2 PASS。
- 最終**18唯一方法＝15新增＋3必要回歸**，逐方法最後狀態全PASS。中間重跑、27反例、合成actual物化及真實兩個as_of不額外當成測試方法。

三個原core回歸僅：`test_complete_vs_truncated_prefix_identical_with_future_mutation`、`test_basis_reset_stops_old_comparison_reference_and_volume_baseline`、`test_caller_manual_answers_and_strategy_promotion_refused`。沒有重跑舊完整suite或已結清工程。

## 發布與自審

只發布程式、合成fixture／actual／測試log、原檔指紋與非行情白名單摘要。新CLI拒絕任何Git工作樹（含symlink解析）內的真實輸入／輸出，新目錄／檔案建立不覆寫。完整回應、轉接payload、core結果與衍生價位沒有加入Git。保存前掃描本輪全部路徑、比對真實行情列序列與真實結果fingerprint不曾出現在公開變更，檢查token／私鑰等敏感模式；固定SHA讀回在完成後回覆。這不是取得散布授權，也不是防任意外部使用者複製資料的通用DLP。

受保護11檔及事前input／expected原bytes不變，baseline.json可查；原core/__init__、graph_core_chart、官方原件／source契約、全部capital研究及舊資料庫未改。正式false、primary_pressure_id=null、70拒算／2不足／其中8換股影響未支援／真實合格總淨0、1101期初權利UNKNOWN及來源parents保持。

## 拒判、未讀與未支援

缺／零價、矛盾OHLC、重複／倒序／越界／非法日期、缺已知交易日或精確as_of、缺量／非整數量、來源／基底錯配、缺警告、同日／未完成日、未知取得時點、假造historical資格及scope擴張明確拒絕，不補值。真實本例沒有來源取得阻塞，但仍是RESEARCH_COMPUTED_NOT_QUALIFIED，非正式買點。

Work M2-2報告與證據ZIP在Library，正式工具未提供本輪可用入口，**未取得／未讀**；未HTTP試探、不要求搬檔。本輪實讀官方Technical文件，條件沿用使用者已核Free個人非商業範圍，未獨立認證資料散布權。8069價格一致僅Work摘要陳述，本輪只核實官方量精度；不能冒稱已重驗其精確股數。

完整歷史股票母體、即時／未完成K、歷史公布時間、完整公司行動／Adjusted、跨基底連續圖形認證、正式圖形品質、全市場選股、策略／勝率／風險閾值、真實績效／自動交易均未完成。本輪沒有市場帳務回放、合成帳戶變更、UI／Android、全市場擷取、付費／註冊／部署／下單或對外訊息。驗收達成本里程碑即停止，不自行接下一任務；不需使用者操作或例行轉貼。
