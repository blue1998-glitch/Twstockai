# 數量候選受控逐輪合成回放 0.1

本輪唯一能力是把既有quantity_candidates/0.2完整研究閘門接到既有execution/0.8，逐輪從原帳實際回放結果重新產生候選。不是自動策略、比例選擇、委託產生器、新執行／會計或來源認證引擎。原trend_replay與九路徑保存結果不改、不重跑；本接口不採用其固定限價帶或policy選擇。

## 輸入 capital-quantity-replay-input/0.1

固定欄位：schema、synthetic=true、initial_account、origin_ledger、ledger_close_proof、run_policy、rounds。

run_policy有version、parameter_source、available_at、max_rounds。可知時間不得晚於首輪決策；明示計算預算1～8輪（工程資源界線，非固定檢討次數／交易規則），超限整次拒絕，不截斷。

每輪固定欄位：id、decision_template、quantity_template、selection、orders、tape、observed_until、cancelled_order_ids。

- decision_template是0.8決策輸入，明確含decision_at／data_cutoff／來源／證據／當期review／模型／限制，但禁止account、plans。首輪account只取initial_account；後續只由原make_checkpoint／account_at_checkpoint取得，cutoff必精確等於前輪watermark。不從新NAV重開本金，不填行情／時間／權利。
- quantity_template是0.2請求除decision_input與continuation以外的欄位；batch_context另禁止account_id／origin，由原帳指紋及是否有原checkpoint機械綁定。phase與其餘來源／可知時間仍由輸入明示，不自動選FIRST或追加。不得塞candidate快取、raw plan、family、外部checkpoint或同區間reassessments。
- selection固定mode、sell_A、additional_B、reason。mode可GRID（按兩個明示股數找同一目標）、HOLD、EXIT_A_KEEP_CASH、FULL_TRANSFER；後三者股數欄須null，按既有kinds找候選。reason須明示合成意圖來源，不是最佳數量理由。沒有預設／fallback／argmax或ranking。
- orders完全由合成輸入提供，含既有0.8所需股數、限價、決策／送出／到期時間。接口不造單、不定限價帶、不設定批次或比例；0.8核對其數量／時序與候選，不能以netting或其他股票委託超出目標。
- tape、交割日期與close proof均由輸入明示，逐輪市場欄位不從未來推定。不補價格、成交、交易日曆、T+2、日終可知鐘點或零事件。
- cancelled_order_ids也是明示研究輸入；首輪須空。後續只交既有continuity檢查，接口不自行取消或重下舊單。未明示處理的活單／期初應付等原未支援情況保留並停止。

## 回放順序與停止界線

每輪先綁原帳，再生成0.2候選，精確找輸入指定的候選。只有CURRENTLY_FEASIBLE或WAIT_SETTLEMENT_REASSESSMENT且外層feasible_for_research=true才可委派0.8；內層core_evaluation可行不能繞過外層batch gate。被拒絕／未支援不改選續抱，不執行新委託，也不假裝零成交成功。

WAIT可觀察／執行符合原模型的賣出腿；原0.8保留買單requires_reassessment，交割到款後仍不得直接買。下一輪必須有新帳／cutoff／review／候選閘門；如要提出新批次，原單須按輸入明示到期或取消，新增批次另核獨立觸發。延續同一條合法條件買單的中途重評由舊引擎原接口處理，但此新橋尚未接入，明確不接受同區間reassessments，不能繞過0.2。

只把選中候選的研究plan放入新副本交給原simulate；沒有生成orders。持有A-zero時plans保持空，避免重複內建ID。核對回放decision_id必等於該候選的core_decision_id。成功才用原make_checkpoint保存原始opening、fills、權利、未成交order、reserve、latest及全部token，供下一輪機械承接。

停止狀態分STOPPED_CANDIDATE_GATE、STOPPED_NOT_IMPLEMENTED、STOPPED_INPUT_ERROR、STOPPED_EXECUTION_REFUSAL。不繼續後面的輪次，不把曾請求取消視為已生效；只有實際委派成功的0.8結果才可能記載取消。錯誤時前輪execution／checkpoint仍作歷史證據保存，**不是含本輪新宣告的可續接狀態**。本版不提供從停止結果或外部checkpoint跳過拒絕輪的resume接口；需修正完整明示輸入重新研究，不能丟掉新限制。

## 輸出 capital-quantity-replay/0.1

replay含逐輪generation、明示選擇、實際委派job、原execution與checkpoint、停止原因、execution_calls及最後已回放watermark。COMPLETED_PROVIDED_ROUNDS只表示輸入各輪完成，不表示所有單成交／全帳清倉或策略通過。無ranking、最佳比例、真實績效或正式資格，全部false、主壓力null。

每輪numeric_prefix為明確比較範圍：候選research、所選ID／分類、明示orders、原fills／events／states、截至watermark的原ledger及checkpoint.state。完整origin／raw execution／checkpoint的雜湊另作保存完整性，未來尾段可令它們不同；不改寫原0.8結果或剝除其ID。相同合法當時前綴、截止後行情分別改A漲／B漲／雙跌時，numeric_prefix須一致。

一般READ直接讀保存JSON，不呼叫引擎重算。先保存契約、input／expected及來源版本，再實作與執行；新actual不覆寫舊producer／oracle／log／manifest。

## 有限驗收與保持

部分成交後獨立新事件再評、到款未重評不買、到款後新review與明示取消／新委託正例、舊事件／偽FIRST／共柱追加被擋、漲停未成交、原股賣不出時共同途中風險、原帳應付未支援停止、日終尚不可得拒用、禁止account／raw reassessment注入、未來隔離與輸入不變。自審資金／權利／成交／時間接線，不預設轉Work。

不擴張R2/F、信用、來源認證、完整外部既有單／期初應付或不中斷活單承接能力。1101 2026-01-02期初cash_claims仍UNKNOWN／拒算，不找公開來源、不收私人文件。正式action_resolution0.4、來源0.10及parents、70／2／其中8／真實總淨合格0、原圖形／人工契約不變。不bootstrap、真實producer、舊suite／九路徑、市場績效、UI／Android／樣本外、部署、交易、付費或發訊息。
