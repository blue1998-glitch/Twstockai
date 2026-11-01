# F-01 修復、實際驗證及界線

## 結論

F-01已重現並修復。不可比舊箱的pressure_distance_fraction／relative_width_to_anchor與已停止高點的distance_to_anchor均改null；另有anchor_comparison_reason，不補0、不把跨基底價格視為可比。

修前／修後均使用GitHub既存TWSE2884官方月表，2026-03-01～07-22；原件SHA與既存meta一致。重用M2-3`_retained_sources`及`source_audit.parse_twse_month`的只讀來源核對，不進FinMind擷取／RUN。明示07-01不比價中斷不推定公司行動類型。兩截點是同一案例相鄰快照，非獨立市場樣本。

| 截點 | 供應日線 | 不可比舊箱 | 已停止舊高點 | 舊箱pressure距離非null 修前→修後 | 舊箱相對寬非null 修前→修後 | 舊高點距離非null 修前→修後 |
|---|---:|---:|---:|---:|---:|---:|
| 2026-07-21 | 97 | 3 | 4 | 3→0 | 3→0 | 4→0 |
| 2026-07-22 | 98 | 3 | 4 | 3→0 | 3→0 | 4→0 |

修前就已正確排除不可比舊箱於目前relevant_pressure_ids，修後保持，不誇大為已發生錯誤交易。primary_pressure_id=null、classification_quality=NOT_VALIDATED、action_qualification=NOT_EVALUATED。

## 變更範圍與保全

輸入仍graph-recognition-input/0.1，新的數值結果graph-recognition-research/0.2／result_id明確換版。只在`_compare`用既有usable_at_anchor分支，`analyze`高點參照用原trace_reference.last_relation分支；trace_reference本身完全未改。兩個可比公式保持原文，只在不可比時不求值。新增reason為原停止事件類型，可比時null；停止的原日期與路徑保留。

12個其他函式原文與DEFAULT_CONFIG原文完全相同；原反轉百分比／箱型門檻／候選列舉／壓力篩選／Pareto／主壓力資格、原帳與交易程式未改。6個合成案例及2個真實截點，除事前授權三欄、reason、schema_version／result_id外，全結果canonical指紋逐值一致；每個可比物件的三欄另逐值等同修前，不只核物件數或終點。歷史ID、順序、幾何、轉折、形成時點、全部事件／停止路徑、局部volume／downside及候選關係保持。

先保存CONTRACT、cases／expected與baseline，再執行before；未修改oracle迎合結果。修前core原件與真實完整輸入／輸出只留Git外；synthetic-before原件保留。舊0.1結果與M2-3 manifest／actual／log均未覆寫，不要求舊source指紋與新core相等，不以新版靜默重算歷史。

## 本輪實際測試

12唯一方法首次全PASS＝8新增＋4必要既有回歸，詳tests-targeted.log；本輪沒有測試失敗或失敗修正紀錄。before故障是成功重現原缺陷，不計FAIL方法或新增PASS。六個案例／兩個真實截點不另外算測試方法。

新增：明示中斷、缺價、已知缺日、同基底／中斷前數值相同、錨點當日中斷、前綴／未來修改與input不變、完整允許差異／資格核對、凍結與來源保全。

原回歸只選4項：`test_complete_vs_truncated_prefix_identical_with_future_mutation`、`test_confirmed_geometry_and_prior_events_survive_append`、`test_occurrence_before_confirmation_and_no_future_point_before_confirm`、`test_caller_manual_answers_and_strategy_promotion_refused`。未重跑舊18全套、81市場條件、13敏感度、資金帳務研究、UI、producer或市場回放。

## 保存與未解決事項

起始原工作區`/workspace/Twstockai`、原分支`dev/m1-v018-chart-annotations`，本地／遠端同`df4e4b5dc4a6c01e984fbe973701cb066615eae9`且淨；未見其他活躍工程程序，這不證明平台外絕無寫入者，保存前另核遠端。只由原Codex，未開代理／worktree／分支或平行引擎。

發布僅核心最小修正、合成資料與非行情驗收摘要、必要文件；不發布FinMind行情／真實完整輸出／新可還原行情衍生數值。原來源、10個受保護相依檔、既存保存結果與根交接舊bytes保持；敏感掃描及本輪路徑自審完成後正常commit/push與固定SHA讀回，實際SHA在交付回覆及Git提交中，不另建封包。

Library`Work_M2_4_Real_Graph_Quality_Validation_20261101.md`、ZIP及內附最小handoff／重現程式未取得／未讀；正式工具沒有本輪可用Library入口。依明示規格及庫內原碼／官方原件重現，不要求搬檔，不冒稱Work已核本輪原件。

F-01範圍無未解決阻塞。歷史historical_available_at／完整日曆／公司行動類型仍UNKNOWN；不認證跨基底價格、正式圖形品質、買點、勝率或市場績效。1101 UNKNOWN、來源拒算與全部parents、70拒算／2不足／其中8未支援／真實總淨合格0、正式false／主壓力null不變。M-R1早期弱化不接正式規則，M-R2未執行。總監可直接唯讀本固定SHA之原碼差異／摘要／log；人工不需操作。本里程碑驗收達標即停止。
