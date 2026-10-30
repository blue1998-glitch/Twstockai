# 0.3結果至數量候選的受控轉接0.1

基線51e6db4798ab4c3099200f14632a718b49f818a6。純API `quantity_after_retry.generate_after_retry(request)`，只把已完成的合成review0.3原件接到既有`quantity_candidates.generate`0.2；不重寫產生器、會計、風險、原schema或交易規則，不選勝者、不建單／成交。

## 輸入與窄範圍

`capital-quantity-after-retry-input/0.1`，synthetic=true；欄位固定為schema、synthetic、saved_result、checkpoint、predecessor、decision_template、quantity_template。

saved_result須為已完成的review0.3，不能用停止前prefix、摘要或0.2舊wrapper替代。checkpoint必為完整0.8：含原origin_ledger_input、execution_result與integrity；必須與saved_result的精簡checkpoint、原execution／job／clock／orders一致，並通過原`validate_checkpoint`。這是新數量RUN的原帳核對，不是READ隱式重算／遷移，也不認證任意外部來源造假。

predecessor綁完整saved_result ID、execution ID、checkpoint ID、latest decision/account和完整reviewed tokens，沿既有`conditional_retry.predecessor`語義。遭拒decision不當latest。無活單、無purchase_payable、原incumbent仍有正持股才接；既有無來源限售解除等能力仍依原機制拒絕。新來源不得改標synthetic繞過資格。

decision_template不接受account／plans或委託、回放、checkpoint覆寫。cutoff精確等於checkpoint watermark，decision必在已可知日終之後。來源／價格基底／調整版本與原job相同，當期估值mark須與原ledger同截止報價相符，不補價或重新估本金。帳戶只委派原`account_at_checkpoint`導出，保留現金／股份權利、一般reserve與所有持股。

quantity_template沿原0.2有限整股域、policy／來源／available_at／edge與計算上限；重用原`quantity_replay._quantity_request`建立請求，account_id及origin由原帳導出。只接受ADDITIONAL_BATCH；destination綁原C買單股票，incumbent必與之不同、原帳仍有正持股。不能改成FIRST_ENTRY、family E或同單豁免。所有歷史tokens灌入當期請求，再由原resume／事實歷史核新獨立觸發。

## 輸出

`capital-quantity-after-retry/0.1`，包含綁定資訊、原帳導出的account、完整quantity_request與原generation，不複製生成／會計公式。GENERATED只表示完整列舉完成，不等於所有候選可行；分類、拒絕理由、等待交割及超限沿原產生器。停止時保留已驗階段與原因，不回退成成功續抱。

原資本1430與當期估值1425.100分開；不得把當期NAV當新期初本金。所有候選共用同一原帳與預算，不代表可以同時成交。ranking／selected_id始終null，正式資格false、主壓力null；不生成orders或fills。原歷史orders／fills僅保存在來源checkpoint中。

## 定向證據

先凍結原件路徑／指紋、精確template／edits、materialized input指紋及expected，再實作與執行。來源重用已保存0.3成功原件及new-batch完整checkpoint，不重跑原retry或市場producer。四格明示合成域sell_A=0..1／additional_B=0..1，加原續抱／退出／全換端點；這是工程fixture，不是正式比例或門檻。

必要驗收：獨立新觸發通過完整外層閘門、舊觸發拒絕新增B、錯latest／缺token／偽首次／錯基底／截止／mark／手填account拒絕、停止前歷史帳拒絕、原A為零／活單／應付範圍阻擋、搜尋超限與UNKNOWN資格不被放寬、完整原帳／來源／receipt／token保持、輸入不變、只改完整性metadata不改數值候選。活單／應付／零A及破壞checkpoint的變體只屬結構拒絕診斷，不冒稱有效新回放或成交actual。

原來源0.10與parents／正式action_resolution0.4、1101期初cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、圖形／人工契約及全部正式false/null保持。無R2/F、期初應付或外部活單擴張，無私人文件、新來源、bootstrap、舊suite／九路徑、真實producer、UI／Android、樣本外、部署、交易、付費或訊息。原唯一Codex／原工作區／原分支，依既有里程碑自審及正常保存讀回。
