# M2-5 F-01｜跨中斷的相對錨點數值（修前凍結）

唯一變更：不能與目前錨點比較時不產生相對錨點數字。輸入仍graph-recognition-input/0.1；新結果版本graph-recognition-research/0.2，舊0.1保存結果原樣READ，不遷移或覆寫。

| 物件 | 既有不可比判斷 | 新欄位行為 |
|---|---|---|
| 舊箱 | usable_at_anchor=false／anchor_relation=NOT_COMPARABLE_AFTER_GAP | pressure_distance_fraction=null、relative_width_to_anchor=null |
| 舊高點參照 | path.last_relation=NOT_COMPARABLE_AFTER_GAP | distance_to_anchor=null |
| 仍可比物件 | 原判斷仍可比 | 三個數值各保持原值與公式 |

箱與高點參照新增anchor_comparison_reason：不可比時為OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP，可比時null。沿既有停止事件／路徑查實際日期；不推定公司行動類型或補0。舊箱繼續排除目前相關壓力；primary_pressure_id=null。

不改反轉百分比、箱型條件、候選選擇、形成幾何、ID、歷史高低點、事件、局部統計、Pareto／親子關係或任何交易資格。除結果版本／result_id、上述三個目標欄位及新增reason外，修前後完整結果逐值等同；可比物件三欄另逐值相同。

先凍結cases.json／expected.json／來源指紋，再執行before保存修前actual，然後才修程式。合成案例覆蓋：明示基底中斷、缺價、已知缺日、無缺口、中斷之前、錨點當日中斷。另核同前綴／未來改寫、原事件保全與原相關候選排除。只跑本次定向及直接相依回歸，不重跑舊18／81／13或資金研究。

真實案例只重用GitHub既存2884官方3～7月月表，SHA與原meta對照，裁至2026-07-22；07-01明示不比價中斷，07-21／22分析。沒有新擷取行情、不讀取或發布FinMind原始資料。即使資料曾在Git，本輪真實完整輸入／輸出及可還原行情的距離仍只存儲存庫外；公開只版本、狀態、筆數、欄位非null計數及保全布林。

Work M2-4 Library報告／ZIP／reproduce_field_issue.py未取得／未讀，不假稱已讀或要求使用者搬檔。來源及歷史可得時間UNKNOWN、classification_quality=NOT_VALIDATED、正式false／主壓力null、1101與70/2/其中8/真實合格0保持；不執行M-R1策略接線或M-R2。F-01與相依回歸達標即停止。
