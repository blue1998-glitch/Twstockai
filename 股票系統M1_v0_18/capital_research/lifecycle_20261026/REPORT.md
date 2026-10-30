# 功能交付：原批次生命週期唯讀摘要

基線3b025c6a94a65fdb3cd1f0afa023dbaacb5d1374。遠端／本地相同、初始tracked／index／untracked皆0；指定祖先保留。只有新lifecycle.py、lifecycle_read.py及本輪證據與既有接續文件的新有效段。原quantity／conditional review／core／execution／action_ledger及舊原件不改，沒有執行producer。

## 可用能力

`lifecycle.summarize_saved(saved)`把已保存quantity replay及原條件單review結果整理成JSON；`lifecycle_read`可直接輸出中文文字表。兩者沒有RUN、補價、重算、修復或下單路由。檔案IO只在CLI，核心僅標準函式庫；不是第二帳或新策略。

原提案只列一次並列出共用提案的order IDs，原單各自列核准原單量、實際成交、活單剩餘、取消／到期、待交割、交割未知、預留及重評理由。同單review保持原order／origin decision；新批次r2-B另列，不併回r1-B，不把每單當成各有整筆研究預算。核准量不是新的追加資格或正式授權。

帳戶現金、一般reserve、應收應付、實股、cash／share權利、origin資本、latest及全部tokens照原row與state保存，歷史snapshot各有截止／可得時間。一般與單筆預留不能加回現金；原嚴格可用額不是可追加金額。終止單remaining分到取消／到期，活單量明示0，不復活舊單。

每筆fill保留原股數、價格、費稅、交易／明示交割日與JSON pointer。只有journal中同fill的結清記錄才列已結清；未到明示日期則按保存排程列待交割；已到日卻無逐筆結清紀錄列UNKNOWN。缺逐筆待付款額保持null，不用price×shares或全帳應付重建。來源指紋與可用能力／正式授權分開。

## 實際證據

最終`after-final/summary.json`的19個READ案例符合凍結expected；其中13份為直接讀既有保存原件，6份為明示結構診斷變體，不是新引擎結果或市場樣本。新input.json使用原件相對路徑、byte長度與SHA及明示mutation規格；不重複搬運原JSON或重跑原producer。變體的具體操作在fixtures.py，在第一次讀取前已保存版本；初始規格與expected實作前凍結，未知status案自審後另存status-intake才執行。

|保存例|本輪摘要直接顯示|
|---|---|
|partial-pending|原B20，實際B7，活單13，預留261.65039，按原排程待交割7；已結現金596.500、應付141.140、嚴格可用455.360、一般reserve100；cash80及A10權利保持。|
|settled-cancelled|原B20，實際B7，取消13、活單0；B7有PURCHASE_SETTLED的141.140原journal。已結現金535.360，應付0，原到期cash80／A10已交付，無重建帳務。|
|full-pending／waiting／limit-up|分開原單全成交但待交割、尚待重評未成交、重評通過但漲停未成交；不把通過review視為成交。|
|rejected-conflict|拒絕attempt、NEW_CAPITAL_NOT_QUALIFIED:B、當期資格、restriction_conflicts及decision_at／observed_at分開保留。|
|expired-and-new-batch|r1-B實際7、到期13；r2-B實際1另列。總買入8，不把前後snapshot重複計成交；共享提案只列一次。|
|cancel-and-new-batch|r1-B取消20，r2-B新單1；原單與新批身分不混用。|
|stopped-historical|新觸發遭拒，摘要明標HISTORICAL_BEFORE_STOP並保留NO_NEW_INDEPENDENT_TRIGGER；歷史帳不當新批成功結果。|
|no-execution|NO_SAVED_EXECUTION，account=null及空單列，沒有補成零資本／零權利。|
|missing-settlement-proof|明示結構變體：交割日已到、無逐筆journal，交割未知7、已結清0；帳戶應付仍照原141.140。不是新增真實帳務結果。|
|unknown-schema／unknown-status／corrupt／missing-payable／quantity-conflict|UNREADABLE，清空可誤用的帳戶與單量；不降級補零或回呼引擎。|
|三個未來價格分支|只讀既有A勝／B勝／雙跌保存結果，當期orders摘要完全相同；沒有重跑未來隔離producer或改寫原ID。|

## 測試與自審

最終`tests-after-final.log`：13個唯一方法通過。首批`tests-final.log`及其同bytes副本`tests-initial.log`都是同一次12方法紀錄，不加倍。自審補齊停止理由、現金預留說明及未知status後，本輪相關讀取測試再跑13，實際方法執行25次、唯一方法13；沒有失敗方法，沒有累加歷史PASS、19案例或副本。

fresh-process測例在import階段攔截graph_core、rotation_research及其他capital數值模組，並以audit hook拒絕檔案寫入／刪除／改名、子程序及網路連線；`python -B`讀取CLI仍與保存摘要完全一致。CLI使用-B避免Python自己產生快取，應用沒有寫檔路由。其餘測例驗原input不變、金額／權利／reserve照抄、逐筆結清證明、原單與新批分開、停止／未知拒絕及source pointers。

指紋驗證只是標準JSON保存完整性，沒有重新執行原continuity或ledger。原帳與各保存邊界逐項對應；這不證任意分叉、來源真偽或所有盤中資金路徑。原停止原因或舊限制不因摘要可讀而解除。19個案例及source版本、契約、根舊文及舊原件指紋由self-review及CHANGE_MANIFEST核對。

讀檔期間曾遇exec-server transport disconnected；正式runtime仍顯示running，唯讀重試恢復同一/workspace/Twstockai，HEAD與已保存18案均保留。沒有建立別的工作區、重建原件、bootstrap或要求人工操作。

## 限制及下一步

只接受兩種已明列wrapper及execution0.8／checkpoint0.7；其他schema不隱式升版。缺原提案綁定時核准量UNKNOWN；摘要不做來源認證、新批核准、原始會計正確性重驗或市場成效比較。沒有新增UI、觸發規則、比例、持有天數或策略勝者。

1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0、正式false、主壓力null與所有原parents保持。R2/F、信用、期初應付及外部活單等未支援不擴張。舊suite／九路徑、真實producer、資格重算、市場六方案、UI／Android及樣本外執行0。Astra與第一工作區救援原件未取得／未讀；原唯一Codex自審，不冒稱Work獨立驗收。

可留在Codex繼續：做已保存摘要的唯讀並列入口，先驗共同帳戶／觀察截止／外生市場路徑，條件不一致就拒絕作同條件比較；不評分、不選勝者、不重跑回放。此下一步尚未工程，需要使用者接續指定。
