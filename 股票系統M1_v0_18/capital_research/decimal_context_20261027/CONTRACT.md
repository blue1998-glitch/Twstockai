# 全帳戶評估數值環境隔離修復0.1

基線829fd4af25e12f061e49e0c77446ed2ac4528119。本輪依全專案進度盤點選擇既有純數值契約的必要修復，不新增策略、行情、READ或並列功能。原account_metrics的`localcontext()`只設prec=50，仍可能繼承呼叫端rounding、traps與指數範圍；先定向重現，不把推導當actual。

## 凍結輸入及預期

明示重用已保存`quantity_replay_20261026/cases/partial-then-independent/actual.json`及`account_metrics_20261027/final/saved/complete-partial-chain/result.json`正常評估原件。input.json保存精確path／bytes／SHA、evaluation_at與四組呼叫端Context；不回放或變更原始帳、權利、reserve、latest或token。所有原件仍是合成研究。

同一份有效輸入，不因呼叫端的低精度／ROUND_UP、Inexact trap或狹窄Emin/Emax而改變本函式結果或拋出例外。每組預期皆與原正常環境保存結果完全相等，包括evaluation_id；呼叫端精度、rounding、traps、flags等必逐欄保持，不以全域setcontext污染它。缺資料仍維持既有REFUSED／null。

若重現，只固定account_metrics.evaluate_saved內部數值Context：50位有效數、ROUND_HALF_EVEN，標準Emin=-999999／Emax=999999、capitals=1／clamp=0及原標準InvalidOperation／DivisionByZero／Overflow陷阱，其餘flags清空／traps不繼承。這是重現既有正常環境的計算口徑，不是交易／風險門檻；不改費用、回撤、恢復或權利公式。

實作revision可標0.1.1；輸入／輸出schema仍0.1，正常舊數值／簽章須完全相同。舊READ繼續讀原bytes，不補算或隱式修正既有結果。其他engine的Decimal行為不擴張修改。

## 有限驗收

before保存原source、原件指紋、四組精確輸入環境與actual；不能重現則保存反證不修改。after另存相同spec輸出；不改oracle、before或歷史log。只測環境隔離、呼叫端及input不變、缺資料拒算、既有evaluated_replay之評估接線／READ不重算；不重跑整套8／14／8或真實producer。

原1101期初cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、正式資格false／主壓力null及來源／圖形／人工模式限制保持。沒有來源認證、帳務擴張、R2/F、未定續抱／移轉策略、UI／Android或樣本外。原唯一Codex依里程碑自審、正常commit/push及固定SHA讀回；無人工操作需求。
