# 0.3結果接回數量候選：入口

已完成純API `quantity_after_retry.generate_after_retry(request)`，輸入`capital-quantity-after-retry-input/0.1`，輸出`capital-quantity-after-retry/0.1`。從已完成0.3原件、相符完整checkpoint與當期模板，導出同一原帳／latest，再交既有數量產生器0.2；不重寫生成器、不建單、不成交或選比例。

- [獨立新觸發：完整候選白話表](views/new-independent-trigger.txt)、[完整actual](after-final/new-independent-trigger/actual.json)。
- [舊觸發：新增買進仍拒絕](views/old-trigger.txt)。
- [當期資格UNKNOWN：新增買進拒絕](views/unknown-qualification.txt)。
- [20案最終索引](after-final/summary.json)、[事前契約](CONTRACT.md)、[報告](REPORT.md)、[6唯一方法log](tests.log)、[最終證據補驗1方法](tests-final-evidence.log)。
- [自審](self-review.json)、[來源／輸入凍結](intake.json)、[原A補強反例凍結](role-binding-intake.json)、[檔案指紋](CHANGE_MANIFEST.json)。

明示四格只是工程fixture：sell_A=0..1、additional_B=0..1；另沿原流程列續抱／退A留現金／全換端點，不代表建議比例或策略。原資本1430與當期估值1425.100分開，現金275.100／預留100、A60/B25/C2及12個歷史token保持；不是從當期NAV重開本金。

僅限無活單、無應付、原A仍有正持股，且原核准提案可明確追溯唯一原減持股票。不能把C等其他持股改叫原A，也不能改稱首次買進。停止前歷史帳、精簡checkpoint、錯前身／token／估值／基底或來源都拒絕。後續一般回放resume、新交易與原未支援帳務不在本版。

案例input採完整來源指紋＋精確模板／edits，`materialized_input_id`綁定實際純JSON API輸入。外部`fixtures.materialize`只讀庫內固定原件；生產API沒有檔案／網路IO。不要求搬檔，也不重算原retry或任何市場回放。

`after-final/`綁最終source。`initial/`、`before-role-binding/`、`after-role-binding/`及`after-role-final/`為中途歷史；原A防線修前兩案會生成，首修欄位錯誤的actual／診斷也保留，oracle未改。最終20案符合預期；6唯一unittest方法通過，換綁最終actual後只補1個相依方法，7次執行不算7唯一。所有正式資格false／主壓力null，合成結果不代表策略有效或市場績效。
