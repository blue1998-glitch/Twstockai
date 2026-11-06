# 數量候選受控逐輪合成回放0.1：功能里程碑

本輪接續bca6409c72b5eebefe9532877033b25d6a6b879b，只新增quantity_replay薄接線，原quantity0.2、core／execution0.8、continuity、風險／會計與原trend_replay全部不改。起始工作區乾淨，原唯一Codex／原分支及/workspace/Twstockai；本輪依功能里程碑授權完成自審、正常保存與GitHub讀回。

## 實際改善

原0.2能列出可檢查數量，但尚無回放入口保證外層batch gate先於原執行器。新replay_sequence接收明示選擇、合成orders／限價期限／市場觀察，先重算當期數量閘門再委派0.8；後續account只從原執行結果的checkpoint導入。不選策略或數量，不採舊trend_replay的固定限價帶，不產生orders，也不假裝所有目標已成交。

最有用的例子：第一輪A賣50／B買20的明示意圖，只實際賣A20、買B7；下一輪從A80／B7／C2與原權利、現金1056.66、reserve100重評。新獨立事件與明示B1訂單通過後，原帳終點A90／B8／C2、現金1115.64；A10原待交權利與80原應收已由既有帳交付／付款一次，不是新投資收益。

等待例：初始現金100全保留，賣A50後到款596.5，B20仍WAITING_REASSESSMENT、B持股0；到款不等於重新批准。另一明示路徑在當期新review／獨立事件與明示取消舊B20後，才送入輸入提供的不同ID B1單。原B20保持CANCELLED_AT_REVIEW／remaining20，不能冒稱原單已成交。

## 凍結輸入與實際證據

先存CONTRACT／baseline-sources、17組精確input／expected及intake，再實作bridge並保存source版本。新case actual不改任何舊九路徑、0.2證據或oracle。首次17案有一項錯誤分類不符：禁止reassessments欄被泛用NOT_SUPPORTED字串誤歸成帳務未實作。只修新bridge分類，已知continuity未支援碼才列NOT_IMPLEMENTED；修前source、actual、log及diagnostics保留，oracle未改。修後17案另存after-final，全符合預期。

首批15個方法有14個通過；一個測試要求「raw core可行、外層拒絕」，但原UNKNOWN fixture也沒有新觸發，raw core本身已拒絕。保留原輸入、oracle、actual、失敗log及斷言，另先凍結有合法B-event但phase仍UNKNOWN的outer-only-gate-control輸入／expected，再執行：raw core=true、外層REJECTED、execution_calls=0。只把該方法指向強化fixture，原斷言不減，補跑該一個方法通過；其他14方法原樣不重跑。

所以最終是**18個合成案例、15個唯一方法最終通過**。不是16個方法，不加首17／修前批或歷史PASS；沒有舊suite、九路徑或舊prefix producer重跑。方法內HOLD、超限、缺selection、超額orders等變體只有測試source／log，未冒完整逐案actual。

最終source案例位置：after-final/各案/actual.json。原17案清單／oracle在intake；強化案另在gate-control-intake／summary。source-versions-final及final-with-control的生產bridge相同；只因新fixture使測試方法換一個案例名。修前cases/*/actual與根summary留史，不混成最終結果。

|驗收|最終保存證據|
|---|---|
|部分成交／連續原帳|partial-then-independent：逐輪原始資本2230保持，NAV2230→2226.66→2225.64；現金1056.66→1115.64，C2、原權利、reserve100、fills／latest／tokens接續。不憑終點相等宣稱中途正確，逐輪數值及來源鏈皆核對|
|到款不自動買|settled-not-reapproved：到款596.5後仍B0、舊B20 requires_reassessment=true；wait-then-new-review明示取消及新觸發後新B1成交|
|完整外層閘門|outer-only-gate-control：raw core可行但phase UNKNOWN，未呼叫執行器；false-first-blocked／old-trigger-blocked／shared-bar-blocked皆保留前輪兩筆fill，新輪execution=null，不fallback|
|未成交／途中風險|limit-up-unfilled保持B0；unsold-A-joint-risk中A跌停未賣，B雖OPEN且資金足仍因實股／權利／可能買單共同風險被原引擎擋，A100／B0，不預扣A曝險|
|原未支援保留|opening-payable-unsupported：保留兩筆原fill、141.14期初應付及未成交狀態，停止下一輪，不歸零或重開本金|
|可知時間／身分|close-not-yet-known盤中不得提前使用16:30才可得日終帳；account-reset-refused禁止template帶account重設；embedded-review-refused不接受同區間raw reassessment繞過閘門|
|未來隔離|prefix-only與future-A-wins／future-B-wins／future-both-fall的numeric_prefix完全相同；完整origin／raw result ID可因未來尾段不同，原件指紋不與數值前綴混比|
|輸入及選擇|輸入不變；明示HOLD不造orders；缺selection不fallback；超出回放資源預算拒絕；明示B21超過所選B20時由原0.8拒絕，不改成20或默默成交|

## 集中自審與剩餘界線

本里程碑由原Codex自審，不預設逐輪轉Work。額外複核：所選候選core_decision_id與執行decision_id一致；新account來自原checkpoint；每輪原opening、權利、fees／cash、fills、過期／取消／剩餘單、reserve、latest及全部token均可回查。原0.8數值與風險公式不複製，沒有第二資金帳。首批分類錯誤與fixture不足均如實留史，未修oracle換取通過。

每個未成交／部分成交以原引擎狀態保存，未提交的目標差額不冒未成交單。所有orders都是明示合成輸入，非本接口產生。COMPLETED_PROVIDED_ROUNDS不表示全帳清倉或全部權利已結清；有活單的觀察段也可以完成。所有研究／正式資格保持分離，沒有策略排名或實際績效結論。

新接口只接分段回放。合法原條件單在同區間持續重評雖原0.8已支援，本橋尚未接入完整0.2閘門，所以拒絕reassessments，不繞過。外部既有單／期初應付／信用／R2/F與來源認證等原未支援能力不擴張。停止結果有本輪原quantity_request與generation，前輪checkpoint標示歷史證據，不能跳過拒絕輪當含新事實的resume帳。沒有外部checkpoint或從停止結果resume接口。

未執行：真實producer、來源擷取／資格重算、市場策略績效、舊suite／九路徑、UI／Android、樣本外、bootstrap／hydrate。無私人原件，1101 2026-01-02期初cash_claims維持帳戶證據阻塞UNKNOWN／拒算，不再搜公開來源。正式action_resolution0.4、來源0.10及parents、70／2／其中8／真實總淨合格0、主壓力null、圖形／人工基底及所有false保持。Astra／救援原件未取得未讀，不等待重建或推定890檔。

## 下一步分類

**可留在Codex繼續**：下一項僅接入「本回放已記錄的合法條件單中途重評」與完整數量閘門，原0.8已有合法重評契約，不需決定新比例、買賣門檻或策略勝者；不擴外部既有單能力。本輪未啟動下一項，也無需人工搬檔或提供私人文件。若未來改問如何自動選數量／比例或策略優劣，則需要Work研究，不能由本回放結果制定規則。
