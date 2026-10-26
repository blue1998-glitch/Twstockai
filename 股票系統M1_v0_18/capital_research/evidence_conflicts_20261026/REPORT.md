# 跨輪遭拒宣告限制衝突0.6：定向工程結果

基線及最新已核遠端／本地HEAD為4339a146d22dd849a6131a8c13f08f2e56145a2f。本輪經使用者明確答覆授權重現、最小修復與必要測試；不commit/push。全部差異留在原/workspace/Twstockai，不代表GitHub已有0.5／0.6或Work取得原件。

## 已重現與修正

主三輪反例在0.5實際重現：第二輪期限改null且新增已知撤銷，第三輪恢復原件後B_qualified=true、E_partial_candidate=true，沒有新token。tests-before-one.log保留True != False的實際FAIL；第三輪沒有執行成交，未造1/13行情。

before與after-final各12個合成案例，所有specification／first-input／expected bytes保持一致：

|案例|修前0.5|修後0.6|
|---|---|---|
|mixed-null-revocation|資格及候選放行|兩者拒絕，限制衝突UNKNOWN|
|mixed-later-revocation|資格及候選放行|兩者拒絕|
|rejected-value-revocation|資格及候選放行|兩者拒絕|
|rejected-value-earlier-expiry|資格及候選放行|兩者拒絕|
|alias-after-conflict|資格及候選放行|兩者拒絕|
|independent-new-fact|獨立新事實可競爭|仍可競爭，保留舊root衝突|
|restore-valid-original|有效原件可恢復資格|保持，無新token|
|restore-after-extension-only|有效原件可恢復資格|保持，無新token|
|future-revocation|早期可用、已知後取消B|保持|
|late-revocation|公布晚於成交，B20已成交|保持，不回刪|
|equal-expiry-revocation|到期與撤銷同時，EXPIRED|保持|
|future-no-tape|watermark取消B|保持，at／observed_at分開|

五種錯誤資格放行已重現。後四個時間案例本來就符合預期，是控制及必要回歸，不冒稱新修復。第三輪均有具體decision input／前身／checkpoint，第三輪成交只出現在仍處於原行情視窗的明示早期時序。

原缺陷不是raw宣告遺失：完整fact_sources及observations仍有新撤銷，但遭拒版本不更新root；恢復精確舊原件清除rejected後，issues只查舊root。修復在fact_lineage增加按root保留的restriction_conflicts，並由既有issues／資格／standing單路徑輸出FACT_RESTRICTION_CONFLICT_UNKNOWN。不認證遭拒宣告、不改root、不新增資金帳，也不以新decision_id解除衝突。

數值source改動限fact_lineage及core／continuity／execution版本綁定；eligibility沿原接線使用issues。版本為決策／成交／比較0.6、checkpoint0.5、fact-history0.2。新契約見CONTRACT_0_6.md。

## 實際驗證

tests-final.log：25唯一方法PASS＝13新增＋12必要回歸。修前主單例也在這25個唯一方法內，不計26；不累加歷史35／20／38／51／46或合成案例數。首個完整修後批即25通過，無未解測試失敗。必要回歸精確清單見verify.py及execution.json；未跑整套舊suite。

測試涵蓋固定oracle五個拒絕反例、兩個原件恢復正例、獨立新事實、未來完整數值prefix相同但raw來源不同、可知後撤單、晚公布不刪舊fill、同時到期、無tape時間分離，以及原帳／權利／reserve／latest／token／舊checkpoint拒遷移。所選舊方法另驗有效原件B20、原失效保全、部分成交取消／到期、最新前身、A本股資格、B活單區間拒絕及READ不重算。

主鏈無成交：第一checkpoint現金1000／A100／現金權利80／股份權利A10；第二checkpoint現金1080／A110／既有權利已各入帳一次，一般reserve100、原資本2180保持。不能因這條空委託鏈對帳就宣稱所有中途資金皆未重用。部分成交回歸實跑但沒有另生成一套完整0.6部分成交actual，仍明確保留此證據邊界。

## 保存與未完成

修改前先驗原0.5 manifest186項及after-final24個source，再封存36份source／文件與tracked patch。舊0.5 source指紋對封存原件，不對目前0.6 source；舊證據原件留原路徑。新before／after-final、修前FAIL、最終log、source差異、版本及manifest另存；舊oracle、log及結果不改。

未測：valid_from較晚宣告的獨立案例、完整分叉／更正矩陣、真實producer、資格重算、市場六方案、九路徑／10條趨勢競爭、UI／Android及樣本外。未實作：來源更正認證、自動解除衝突、複雜身份合併、任意造假辨識、R2/F及原未支援帳務。

70拒算／2不足／其中8換股影響未支援／真實總淨合格0、正式資格false、主壓力null保持。Astra與第一工作區救援原件未取得／未讀，不猜890檔存亡。Work尚未獨立讀取新本地原件；本輪不部署、下單、付費、發訊息或commit/push。下一步Work唯讀反駁新root衝突保全與正例邊界，工程仍原唯一Codex，後續須依當輪明確授權。
