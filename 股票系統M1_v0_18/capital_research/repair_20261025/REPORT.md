# 資金研究0.3：定向重現與最小修復

本輪只有原既有唯一Codex，沒有commit/push。遠端及本地Git基線仍`6be4333d490bcccfe952c7606dffb802b76cdd5c`，指定祖先及全部後續保留。不是新的GitHub交付，也不代表Work已取得原件。

## 先保存再修

修改數值程式前，封存原未提交0.2的78檔（完整72個差異檔加相關未改source）、141416bytes source/doc patch及tracked diff。逐檔bytes／SHA見intake.json與baseline_0_2/files；原before／after／log／validation_20261024及來源保持。只用現有標準庫與source，bootstrap／hydrate／舊包覆蓋0次。

七個修前probe均在0.2實跑並create-only保存，含完整輸入／預期／實際／來源版本。原先三個靜態疑點已實際重現；部分成交兩例則本來就成立，未冒稱發現帳務缺陷。

|案例|修前實際|修後實際|
|---|---|---|
|新資金資格|B為NOT_QUALIFIED，C-event仍可行並買B20；既存0.2原件另有NOT_QUALIFIED仍買回A100|每股新投入必通過current review；負例候選拒絕／零買單。原再進場同市場路徑另給明示資格正例，1/19買A100|
|可賣限制跨輪|A100／sellable0，無解除事件，下一account卻sellable100|保存不可賣量，無來源解除則明確拒絕continuation，沒有發明可賣權利|
|盤中日終帳|1/8 09:00 watermark已有日終結清款995，現金1995|不符明示日終即拒絕；延後可知的日終帳在available_at前亦拒絕|
|最新前身|重評新decision作前身被拒，舊初始decision反而接受|新前身可接下一決策及實際下一輪成交，舊前身拒絕；新審閱token不重用|
|明示證據到期|已過明示有效期仍可行並買B20|過期／已知失效不能被新review或新ID復活；持續有效舊事實可保留原ID|
|部分成交後取消|0.2已能承接成交、權利與原始資本|新增定向證據，明示取消剩餘單，只釋放訂單預留，一般reserve100保持|
|部分成交後到期|0.2已能保留到期剩餘量再接續|新增定向證據，EXPIRED_UNFILLED及剩餘量保留，不假造取消或成交|

新對照在artifacts/after；重評後再成交在reassessment-and-next-round.json；有效舊事實正例在old-facts-current-review.json；原0.2再進場只作既存保存件引用，明標NOT_RERUN，不把後來摘錄冒修前新執行。

## 必要修改

core／execution升0.3，新增純eligibility及close_clock。continuity升checkpoint0.2，分開origin與latest身份、逐筆decision紀錄、fill/order連結及一般預留；無來源限售解除明確未實作。trend／trend-policy-competition升0.2，把加碼資格真正接到資金提案；其他股票也要各自明示資格，不從原股續抱推導。仍只呼叫原action_ledger，不新增入帳引擎。

未修改正式交易／圖形規則、P0-3/P0-4、人工模式、歷史schema、來源producer／catalog／庫或UI。舊0.2 builder／verify屬封存版本，在新source上不作舊結果重現入口。新驗證與builder在本repair目錄，輸出只能另建新目錄。

## 實際驗證與診斷

最終38個唯一方法PASS＝33新增＋5必要回歸。命令及完整方法見execution.json／verify.py／tests-final.log。原51／舊46只保存，不重跑全suite；首37批與修正37批不累加，probe／builder／同路徑10序列不算新增方法。

首批37有1個FAIL與2個ERROR：共同市場測例把available_at改成原來同一值，預期差異被反證，已改用真正不同且合法的可得時點；延伸跨輪fixture沒有同步延伸委託期限與明示交割日，已修正合成輸入；新close驗證早於原來源拒算，掩蓋缺淨額的既有REFUSED路徑，已還原先行來源資格拒算。所有失敗log保留，沒有放寬拒算。37修正批通過後，原碼覆核補成交量對帳採精確整數及低Decimal精度反例，最終同範圍加1方法共38通過。

正例包含有資格重新進場、舊有效事實經當期review繼續使用、一般已合格舊單延續、完整可賣帳戶減風險；反例包含缺資格、錯來源基底、舊截止、過期／失效、尚不可知日終帳、錯前身、掉權利、清除一般reserve、未結應付及錯fill/order連結。必要回歸只五個READ／保存衝突／缺淨額／非法輸入／缺價方法。

另以CLI READ讀原validation_20261024/cli-records/execution-v1，stdout與舊cli-READ.log完整bytes一致；沒有數值重算或舊檔改寫。證據在artifacts/old-READ-verification.json。

## 資金、權利與未成交證據

部分成交案例期初2180＝現金1000＋A100×10＋現金權利80＋股份權利10×10。首輪只賣A20／買B7；1/8已結1056.660、A80／B7、現金權利80與股份權利10仍在，A剩30／B剩13未成交。取消或到期只解除訂單預留，一般reserve100留存。

下一輪沿原opening及全部fills追加，後來現金權利入帳一次、股份權利成為A10一次；終點現金2069.720＋A10×10＝2169.720。2180＝2169.720＋實際模擬費稅9＋有效價滑價1.28；一般reserve100仍佔額，可用額1969.720。A10不是遺漏退出，而是既有股份權利於後來交付可交易後的實股；沒有假稱全現金。

未來撤銷資料與未來ledger價格只影響相應完整性metadata，不改當前prefix決策的定向反例通過。沒有宣稱任何未知未來或真實市場已全面驗收。

## 尚不能證明

單一假想再進場市場路徑的兩種資格變體，各五個數量意圖／五輪，共10序列，只為接線正反例，獨立市場樣本0、ranking=null。沒有重跑九路徑45序列，也不預定保留部位、R1或R2最好。

R2/F、信用借還款、期初應付、不中斷外部既有單完整重播、無來源限售解除、真實日終／交割認證及實現曝險配對未實作。真實producer／新資格／市場六方案／UI／Android／樣本外實驗未執行。完整公司行動、個人淨額與期初權利、畸零與既有2884影響、歷史可得與原缺價仍不足；70拒算／2不足／8不支援／真實總淨合格0僅核保存檔。

Astra全文Codex仍未取得／未讀，Work已讀只記使用者提供狀態；無HTTP試探、拒絕重試或要求搬檔。全部外部資格及授權false，主壓力未知保持null。下一步Work唯讀研究驗收，完整可貼指令在根M1_CAPITAL_RESEARCH_REPAIR_20261025_HANDOFF.md。
