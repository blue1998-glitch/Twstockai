# 續播結清後接明示行動：交付報告

## 已完成

基線89df50bc5f5a2a044585938a3976e723b2c5108e；開始時本地／遠端一致，tracked／index／untracked均0。唯一Codex於原/workspace/Twstockai、原dev/m1-v018-chart-annotations完成。本輪是既有能力的完整使用案例與定向證據，沒有新增產品API、轉接層、策略或會計。

從 `standing_orders_20261028/controls/expired-to-Jan8/actual.json` 只讀取完整checkpoint，直接放入原 `cash_action` 的 CHECKPOINT 來源；不手填account、previous、reserve或tokens。新決策時間與當期review重用既有1/8 17:00參數。原origin、close proof及1/9 A/C/B tape與 `cash_two_rounds_20261028/cases/independent-B20/input.json` 全文相同，窗口仍為1/5～1/12；原續播與原producer呼叫0。

先凍結CONTRACT、每案action-input／execution-spec／獨立expected及來源指紋，再evaluate保存checked_action，綁完整請求與checked指紋，才execute。新RUN內重新核對checked結果是既有明示執行契約，不冒READ。兩正例各simulate1，五反例simulate0，沒有失敗或產品修補。

## 兩個互斥正例

| 原帳後的明示行動 | 1/9已結現金 | 1/9應付 | 1/9嚴格可用現金 | 1/12現金 | 1/12持股 |
|---|---:|---:|---:|---:|---|
| HOLD | 858.86 | 0 | 858.86 | 938.86 | A0/B7/C4 |
| 新B-step2獨立觸發，新增B20 | 858.86 | 401.40 | 457.46 | 537.46 | A0/B27/C4 |

一般reserve100一直另外保留，表中嚴格可用額未扣該一般預留。新B20成本20×20.02＋原最低費1＝401.40，1/9不能先從已結現金扣掉再在1/12重扣；原80應收也不能提前使用。1/12才現金858.86＋80－401.40＝537.46。原C2股份權利按既有日期到位成C4；HOLD現金858.86＋80＝938.86。兩條路徑是各自從同一原帳分岔，不能共用或加總資金。

原本金1180不變；新行動前當期淨值1178.86另列，不能重設本金。每個日終均獨立核對現金＋應收－應付＋實股估值＋待交股份權利＝既有ledger淨值；新結果的1/5～1/8每日前綴及原fills與前身全文一致。HOLD期末1178.86及新B20期末1177.46只為合成費用對帳，不是策略排名或市場績效。

## 原單、權利與前身保全

- 原 `explicit-order` 的B7成交保持；剩13仍EXPIRED_UNFILLED／reserved_cash=0，沒有復活、撤掉重下或當作已成交。
- 新買進是保存過的 `second-B-buy` 新獨立單，fill ID為second-B-buy-fill-1，只新增20，不是續完舊13。HOLD沒有新委託或fill。
- 新execution_job.continuation保存**完整原checkpoint**，原opening／原始資本／其他持股權利／一般reserve／closed order／fills／fact_sources／重評收據／latest均可回查。舊到期事件保留在該完整前身中；新execution_events依既有job契約，不冒攤平所有歷史事件。
- 9個舊token完整保留，新B-step2的形成點／量柱／事件三個token加入。HOLD當期review同樣會保存新可知證據的token，不等於授權成交或下次可重用。新批仍須新獨立觸發，不能改稱首次。

## 拒絕與必要驗證

五個反例的checked及run結果、拒絕原因與引擎呼叫數全部符合事前預期：舊B-event新批拒絕、假FIRST_ENTRY拒絕、研究B40的預留不足拒絕、錯latest拒絕、仍活13的checkpoint拒絕。B40需801.80，小於已結858.86卻大於扣一般reserve100後758.86，確實驗到reserve，而非只有總現金不足。該數量只是假想邊界案例，不是使用者規則。

`tests-final.log`：4個唯一方法首次通過，核對保存與原件、閘門／呼叫／輸入不變、原帳歷史與tokens、逐日獨立核帳。七案例不是七項測試或七個市場樣本；不累加歷史9／4等PASS。所有新保存JSON讀回一致。舊source、原件／oracle／actual／log／manifest都不覆寫。

產品程式改動0；未跑整套舊suite、原續播／兩輪producer、quantity產生、九路徑、市場回放、真實producer、資格重算、UI/Android或樣本外。數值環境／未來隔離沿未變source已有證據重用，本輪不冒新增該矩陣的證明。

## 限制與下一步

只證這份已結清完整合成checkpoint可直接接HOLD或明示新現金買單。不宣稱所有舊版本、同單0.9／複雜收據／分叉或任意外部單都已驗。仍活單／應付款留在原續播流程；未知期初應付、限售解除、新策略／比例、R2/F、來源認證等未支援不擴張。1/12主例到原窗口末端，不延伸窗口或補新行情。

1101期初cash_claims UNKNOWN、70拒算／2不足／其中8換股影響未支援／真實總淨合格0，正式資格false、primary_pressure_id=null、正式action_resolution0.4、來源0.10全部parents、P0-3/P0-4及圖形人工契約保持。Work／Astra／救援原件未取得未讀，不要求使用者提供私人文件，不推定第一工作區890檔存亡。

本項已完成，無需再新增READ、並列、轉接或協調器。下一個可由Codex核對的具體邊界，是**新批再次部分成交後，以含前輪歷史的root_job重用原續播入口**；本輪不先擴做。策略與數量規則仍由Work及使用者研究。一般工程不需要使用者操作或Work逐次驗收。
