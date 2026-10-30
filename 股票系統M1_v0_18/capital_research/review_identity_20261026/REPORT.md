# review同ID異內容：研究接線0.8（本地未提交）

固定基線 `2ca618a15be296821b02ba139c2ee194fc51b01e`，原工作區／原分支，起始tracked/index/untracked均0。使用者只授權同job及跨輪定向重現、最小修復、相同內容重送正例與必要回歸，**先不commit/push**。沒有新代理、worktree、競爭分支、bootstrap/hydrate或真實producer。以下為明示合成機制，不是市場績效。

## 實際重現

兩種碰撞都成立，另有更換review ID的控制可排除其他防線先擋住的情況。

|案例|0.7修前保存actual|0.8修後保存actual|
|---|---|---|
|same-job-collision|異內容第二請求被略過；沿舊資格B20成交；僅1筆attempt|明確REASSESSMENT_ID_CONTENT_CONFLICT錯誤，不產生成功execution|
|cross-round-collision|沿用前輪ID的新單重評被略過；新單B20成交；僅1筆attempt|同上，碰撞錯誤|
|same-job-identical|重送無新增attempt；B20只成交一次|保持相同；與刪除重送的結果逐物件相等|
|cross-round-identical|先因舊單號不在當輪orders而報unknown order|可在同一原帳history核對相同請求後略過；舊單仍取消、新單B20只成交一次|
|same-job-unique-control|同一限制改用新review ID，留2筆attempt，買單取消、B成交0|保持相同|
|cross-round-unique-control|新review ID可通過既有checkpoint時序，承接限制，取消新單、B成交0|保持相同|

**碰撞案修後actual的execution=null、B_fill_shares=null，不是「成功execution成交0」或買單已撤銷證明。** 原函式在碰撞處ValueError中止，沒有保存新交易結果；衝突前的合法checkpoint及原輸入另存保留。不得把拒絕錯誤包裝為換股或帳務完成。

## 最小時序與排除其他拒絕

沿0.7 fixture原opening：現金1000、A100、cash claim80、share claim A10、一般reserve100，原資本2180。原ledger與來源／基底、成本、明示日曆、1/12行情終點不變。只有本研究明示tape：1/6、1/7、1/8的A/B容量0，1/9容量100，價格仍A10/B20，交割日明示1/12，沒有1/13行情。

1. 先在1/6 16:00建立checkpoint；first review在1/6 17:00，ID=inflight-review，只有同scope／同B-event的value改寫，不新增限制。1/7 B觀察處理後，拒絕提案而保留有效舊單，容量0所以無成交。
2. 同job案沿舊單到1/8 16:00 checkpoint；second review在1/8 17:00，同ID、另加較早期限1/10 16:00（原1/20）。在review當時尚未到期，body改寫＋新期限使提案不合格並形成限制衝突。1/9處理時，0.7先依ID略過；只換新ID的對照會確實接收並取消，所以不是無法通過checkpoint的假反例。
3. 跨輪案先取得1/7日終checkpoint；1/7 17:00合法續接時明示取消舊B-buy，新單使用next-B-buy，正常原件及當期review恢復本股新資金資格。1/8容量0後再取得完整日終checkpoint，1/8 17:00為新單準備第二請求，只沿用前輪review ID。如此不會因重用order_id、活單跨未觀察交易日、未交割買款或cutoff後隱藏成交先被拒絕。

相同內容跨輪正例重送的是**完整原請求**，包含歷史B-buy及原checkpoint；不改成指向新單。略過不授權舊單復活，也不使用舊帳或重新執行取消清單。

每案的specification／first-input／expected及source-versions均先存，再產生prefix／checkpoint／decision。完整input先存，actual另存。六組before／after-final的first-input與expected均逐bytes相同；版本相關checkpoint／decision ID各自依版本計算。沒有更改oracle來配合actual。

## 最小修復

`reassessment_history.request_content_id`使用原fingerprint對**整份原請求JSON**取指紋；字典key順序不影響，列表順序、account、fact、plan、order、checkpoint、decision、取消清單及integrity metadata等內容都會綁定。沒有自行猜測兩份不同JSON語義相等。

`make_attempt`新增完整request與request_content_id，attempt版本0.2。request指紋不使用本次observed_at／結果作為重送判準；原attempt_id仍完整綁收件與結果。`execution._simulate`先遵守既有資產觀察與fresh decision時間門檻，再對已知ID比較原請求：相同才continue，不同明確報錯。對已知ID，可從order_history尋找歷史單號來核對真正相同重送；**未知ID仍不得藉歷史單號重播舊單**。

`continuity._check_result`除既有指紋與前身、原帳、fills、權利、reserve、token核對，再核原request指紋與保存結果／fact_source一致。decision/execution/comparison升0.8，checkpoint升0.7；fact-history0.3與receipt0.1不變。原action_ledger與fact_lineage未改。舊0.7 JSON READ原樣，不重算、不隱式推導遺失的原請求或遷移checkpoint。

## 實際驗證與診斷

最終 `tests-final.log`：**22唯一方法PASS＝13新增＋9必要回歸**。`verify.py`列出方法ID並檢查不重複。不累加修前單例、首12方法中間批、歷史24／25／35／20／38／51／46或六條合成案例。

`tests-before-one.log`保留修前主例FAIL。`tests-first-fix.log`有一項篡改測例先被原本的「事件遺失receipt引用」防線拒絕，而沒有到原預期的request/source綁定檢查。保留log及 `diagnostics/first-fix-test-original.py`／first-fix.json；只補齊該偽造輸入的事件引用，**原拒絕斷言未改**，最終通過後一道防線。這不是以放寬oracle換通過。

定向覆蓋：兩種碰撞、兩種相同內容重送、兩個新ID控制、未來請求不改早期prefix、key順序、原請求各欄位、篡改後重hash、原帳及全部token、歷史READ。9必要回歸包含0.7遭拒限制保全／備款單取消／正常舊單與合法重評／B7部分成交、帳戶接續、舊單時間區間及READ不匯入engine；沒有重跑完整舊suite。

跨輪相同內容正例有本版完整保存JSON：first-round-actual、inherited-checkpoint、next-decision、second-prefix及checkpoint、最後actual。先前合法取消的舊單沒有復活；唯一新單B20在1/9成交，purchase_payable=401.4、settled_cash=1000；1/12原現金權利80入帳、A10交付，最後settled_cash=678.6、shares=A110/B20/C0、payable=0、一般reserve100、原資本2180。方法逐日核現金／權利／應付／市值對帳，不只比終點；仍不代表完整外部單或任意資本分叉已驗。

## 保存與邊界

`baseline_0_7/files`封存26份原source／交接／原帳模組；inventory含長度與SHA。`artifact-audit.json`核26份封存、26個最終source指紋、六組原輸入／oracle及七個舊證據目錄未變。四個source模組差異在source-diff-from-0_7.patch；舊0.7／0.6／0.5原件及歷史log不改。新證據不要求目前source匹配舊版本manifest。

碰撞處理是已送達原execution流程的請求身分檢查；不是通用認證引擎或獨立消息收件系統。沒有matching tape／未到fresh decision時間的請求不會因此提前影響數值決策；錯單號仍可先明確拒絕。沒有自動改ID、自動合併別名或把碰撞宣告認證為有效限制。出錯後如何由外部工作流重新提交新ID，仍須明示輸入，不偷偷重試或生成成交。

未實作：通用來源認證、來源更正／衝突自動解除、複雜身份合併／完整分叉矩陣、R2/F及原未支援帳務。未執行：真實producer、資格重算、市場六方案、UI／Android、樣本外。正式action_resolution0.4、來源0.10全部parents、P0-3/P0-4、reaction_facts及人工基底保持；70／2／其中8／真實總淨合格0、全部正式false、主壓力null不變。不宣稱市場績效或策略有效。

Astra與第一工作區救援原件仍未取得／未讀，不等待、重建或推定890檔。Work可讀已保存0.7，但未取得本地0.8原件，不稱獨立驗收。無commit/push、部署、交易、付費或訊息。
