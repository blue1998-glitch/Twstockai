# 功能交付：原條件買單重評後續用

本輪基線5783899309e6fd9bba5d05eb7c697c3f12e0b11b，唯讀確認遠端／本地相同、工作區乾淨，指定祖先全部保留。唯一新增能力為conditional_quantity_review.py純接線；沒有修改quantity候選、原執行器、核心、事實歷史、連續帳、來源或正式圖形／交易規則。

## 實際新增能力

原數量回放的最後一輪若有唯一仍待重評的本回放B買單，新入口先重算原完整外層閘門並切出真實日終prefix，再從同一原帳取得當期帳戶。原始核准、剩餘量、limit／expiry、source／basis／adjustment、latest與tokens均綁定。當期plan只允許買原remaining；不能注入帳戶、目標、方案family或新委託。

有效舊事實原ID／內容不變，接受新的當期資格review；這是同一單的延續，不是新批次。原quantity0.2外層UNKNOWN即停止，不能靠原生E方案繞過。重評拒絕仍交原execution保存attempt、fact source及限制；資金到位本身不放行。新批次仍走原quantity0.2獨立觸發檢查。

## 保存actual與必要驗證

`after-final/summary.json`的17個合成案例符合先存expected；`tests-final.log`為本輪實跑16個唯一方法，全部通過。每個方法只跑一次；案例產生及修正中間批不加進方法數，歷史15／14／22／25等不累加。沒有重跑舊整套／九路徑／真實producer。測試中的一項直接必要回歸確認沒有review的原quantity回放仍等待，並用原make_checkpoint驗最終帳，不是重跑舊suite。

|案例|保存結果|
|---|---|
|valid-old-fact|原B20於1/9以同一r1-B成交，new_evidence_tokens=[]；原A50賣出fill保留。1/9已結現金596.500、應付401.400、嚴格可用195.100，另一般reserve100未動；A50／B20／C2，原cash80及A10權利各一次。NAV1325.100，非真實績效。|
|partial-original-order|同單只成交B7，remaining13、預留261.65039；1/9已結現金596.500、應付141.140、嚴格可用455.360。不是把部分成交當B20完成。|
|partial-then-known-cancel|1/9先合法B7；1/12撤銷可知後取消13、預留歸零；已成交B7不抹除。原cash80／A10權利到期各交付一次，A60／B7／C2、現金535.360、應付0。|
|rejected-restriction-retained|當期撤銷使review REJECTED，attempt保留宣告，原B單取消、B成交0。|
|rejected-conflict-retained|同ID改寫且縮短期限但尚未到期，review REJECTED；restriction_conflicts進最終checkpoint，原單取消、B成交0。|
|sale-unsettled|1/6重評時賣款尚未交割，不使用應收作現金。即使之後交割，B仍WAITING_REASSESSMENT，沒有自動批准。|
|unknown-current-qualification|UNKNOWN拒絕，保留REJECTED attempt、未成交remaining20。|
|limit-up-after-review|重評接受但B漲停買不到，remaining20及預留402.0006仍在，未假造成交。|
|basis-change／unknown-order／target-injection|精確拒絕；不能以不同基底、假order或任意目標取得重評權限。|
|outer-gate-refused|原quantity完整外層UNKNOWN即阻擋，原生重評未執行。|
|multiple-live-orders|兩個B活單明示NOT_IMPLEMENTED，不忽略其他單或借其預留。|
|close-not-yet-known|17:00尚不可得的17:30 close proof拒用。|
|future-A-wins／future-B-wins／future-both-fall|只改1/12未來價格，完整numeric_result與1/9控制結果相同；原來源完整性ID如實不同。未增1/13行情。|

## 中間診斷與原件保護

契約、16份原input／expected及baseline source指紋先存於intake；新增衝突案另有conflict-case-intake，亦先存才執行。全部expected及input保持原bytes。第一次只改prefix的watermark、未切tape，被原引擎「Execution watermark before tape」拒絕，14／16未符預期；原cases actual／summary及initial-source留史。修正只在新adapter同步切出tape前綴，最終回放使用原完整tape，沒有放寬原引擎。

第二批check-2已有正確重評結果，但9／16檢查器未通過：原ledger替cash claim加OPENING_RECEIVABLE種類，與輸入權利欄位直接全物件相等不成立。改為原欄位逐一相同且種類必為OPENING_RECEIVABLE；股數權利仍完整相等。首次正式unittest前亦修正尚未交割的手算斷言，分列已結現金、嚴格可用及應付，未改任何凍結expected。check-2-source及結果留史。

初次新source指紋因準備指令cwd路徑錯誤，在該次執行後才擷取並明標captured_after_initial_run；不冒稱執行前擷取。原基線source及input／expected／契約仍為實作前保存。最終source版本於最終案例及正式測試前凍結，見source-versions-before-final.json。

## 自審與限制

額外複核資金／權利／成交／未來資訊：原opening與origin資本1330、一般reserve100、完整fills／order IDs、未成交13及其預留、latest前身與所有tokens沿原continuity。比較有1/8 prefix及1/9／1/12保存實際帳，不僅比較終點NAV。所有會計委派原action_ledger，沒有第二帳或免費資本；這些有限檢查不能宣稱任意市場／分叉均安全。

本入口只有每次一個當期review、最後一輪唯一待條件重評的本地買單。型別只接受原B／E，數量0.2的本輪實際正例為E；C事件追加單續評沒有改family，明示未支援。多活單、已不需要條件重評的舊單、外部既有單及任意外部checkpoint承接未支援。完整更正／分叉矩陣及來源認證未做。

期初應付／限售解除／信用與R2/F等原能力不擴張；最終原帳可以保存新成交應付，但本接口不宣稱支援帶期初應付的新決策。較複雜多次中途review、C單續評與未來宣告身分合併未測。沒有UI／Android、真實producer、資格重算、市場六方案或樣本外。Astra及第一工作區救援原件仍未取得／未讀。

1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0、正式false及主壓力null保持。沒有新來源、私人文件、部署、交易、付費或對外訊息。原唯一Codex自審交付，不稱Work獨立驗收。

## 下一步

可留在Codex繼續：補純讀取「原批次生命週期摘要」，把核准量、累計實際成交、待交割、剩餘／取消量、資金預留及每次重評理由放在同一可查結果，讓後續新批次能清楚區分「原單續用」及「新資金追加」。僅讀原結果，不重算或新增買賣規則；尚未開始此新功能。
