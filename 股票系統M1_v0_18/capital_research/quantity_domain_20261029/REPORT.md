# 明示候選數量域里程碑報告

基線3dfe5b222f47f0798876687808eac98daaabe6f7。起始原工作區／原分支、本地與遠端一致且淨。唯一既有Codex，無代理／worktree／競爭分支。

## 完成能力與差異

quantity_candidates.generate新增0.3分支與quantity_domain純整數驗證helper；0.1／0.2維持原行為。新版本沿0.2 batch／來源歷史機制，核明示單位、通道、parameter_source、available_at、account及兩股source／basis／adjustment身分，再在明示bounds完整列舉合法變動量。格點數在既有上限檢查前計算，不先列整股或靜默抽樣；沒有假設可行性單調。

原cost、risk、core、allocation、execution、ledger與所有帳務公式未改。各合法候選仍委派原閘門；端點同樣受單位限制。EXIT不整除就REJECTED。FULL原端點不合法時NOT_IMPLEMENTED，不能把legacy B94默改B93或宣稱單位最大量已求得。合法grid完整與全換求解是否支持分開。

單位限制賣出／新增股數，不限制目標總持股；保留原A105餘5、B3增加2至5及其他資產／權利。僅假想候選，無新委託、fills、成交或市場績效；新0.3不自動接到舊版選擇／回放入口，不把丟掉domain視為相容轉接。

## 事前凍結與實際結果

先保存CONTRACT、33份精確input／expected、來源指紋及原quantity source快照。before保存舊入口對0.3的ValueError；兩份舊0.1／0.2必要基線只為新分支相容性，沒有重跑舊suite或歷史producer。

33案中32案符合原凍結status。唯一不符為existing-B3-add2：fixture由含完整checkpoint的additional-independent改B持股為3，卻保留原帳B0；原core在單位判斷前正確拒絕「Next account/cutoff resets or drops authoritative cash, rights, holdings or orders」。這不是新功能缺陷，不放寬原帳；原input／expected=COMPLETE／拒絕actual均保留，不改oracle或將原summary標全過。

另存corrections/existing-B3-add2-declared-opening的完整input／expected／來源，再RUN：使用獨立明示合成opening B3、ADDITIONAL_BATCH及未消耗的B-event，新增量2、目標B5，單位閘門通過。這是另一個明示假想起點，不冒沿原checkpoint重設本金。原無活單／應付的first-old-fact-reviewed checkpoint另作控制，origin本金2180、latest及所有舊token精確接續，不改既有權利或原帳。

最終8個唯一unittest方法全過（兩批同集合不相加為16）；fixture組裝診斷不抹除，也不把33案當33項測試。人工9格清單、1000股兩格／無合法嚴格部分量、空grid、所有端點單位閘門、舊版相容與unit1正反例、原帳／批次、來源時間／搜尋上限、完整Context／input不變及新程序邊界均有保存證據。沒有測試失敗後修改oracle；沒有重跑無關舊suite／九路徑／真實窗口producer。

## 支持範圍

- 手工9格完全一致；A1000單位1000時原整股1001點縮成合法2點，在明示上限2內完成，沒有合法嚴格部分A量，不據此判策略落敗。
- 單位不合法的EXIT與FULL不會變可用候選；原HOLD變動0即使原倉有畸零仍合法。
- unit1的舊0.1／0.2完整envelope與事前基線相同；8份相關0.2財務／批次案例與0.3去除新增域metadata後完全相同。這只涵蓋所選原件，不冒整套舊suite。
- 新批重複觸發、UNKNOWN、等待交割、不單調集合、成本／reserve、流動性及共同風險維持原結果；沒有改family繞過新批。
- 無效／未可得／錯帳股基底版本的domain及搜尋超限均在原決策前拒絕；三份截止後不同未來研究結果與主例完全相同，來源完整性metadata另比。
- 兩組完整惡劣Decimal Context的完整結果與正常保存actual相同，caller／DefaultContext／input不變；新程序的無continuation主例禁execution／ledger／回放imports及IO／網路仍可生成候選。
- continuation控制仍會重用既有resume_decision原帳校驗，不能將無continuation的新程序證據冒成所有請求ledger呼叫0；本輪simulate、建單及新成交均0。

## 未完成與保存

仍未完成單位感知全換求解、混合通道、實際普通盤／零股成交與容量取整、畸零權利處理及下游0.3接線；未做市場回放、策略、R2/F、來源認證、樣本外或新增資料。單位是外部明示研究限制，不證真實交易所規則。輸入的N、比例、風險與edge仍外部提供，不批准策略或預定勝者。

70／2／其中8／真實合格0、1101 UNKNOWN、正式false／primary_pressure_id=null、來源0.10全部parents與圖形人工、Work／Astra／救援未讀保持。必要自審後只正常保存本輪相關source／證據／既有交接並GitHub固定SHA讀回，無bootstrap、代理、部署交易付費訊息。無人工操作，不預設Work例行驗收；本項完成後不增加保存／READ包裝。下一個明確能力是有界單位感知全換端點，尚未在本輪擴做。

自審未知來源時點控制：quantity_domain.available_at或每股available_at為null時，修前直接由timestamp拋AttributeError；原輸入／預期／修前結果先存diagnostics，再補明示型別／缺失檢查，最終ValueError帶EXPLICIT_QUANTITY_DOMAIN_AVAILABLE_AT_REQUIRED／EXPLICIT_QUANTITY_UNIT_AVAILABLE_AT_REQUIRED，不推日期。這只修純輸入拒絕語義，不改財務公式。actual／validation／tests.log留初版；final／validation-final／tests-final.log才綁現行main及helper。原已知日期的controls／corrections不重新生成，不把舊source指紋誤稱現行；修前helper原文另存。
