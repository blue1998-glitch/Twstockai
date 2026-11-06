# review請求身分契約0.8

僅隔離合成研究；共用原action_ledger，不新增會計引擎。

- `capital-reassessment-attempt/0.2`新增完整 `request` 與 `request_content_id`。指紋使用原graph_core.fingerprint的canonical JSON；所有提交欄位完整綁定，只忽略字典key序，不推定不同列表／數值字串／metadata語義相同。
- review ID在同一原帳的繼承attempt history中唯一。相同ID＋相同request內容是重送，不能再次授權、取消委託、加token、預留或入帳。相同ID＋不同內容報 `REASSESSMENT_ID_CONTENT_CONFLICT`，不得默默視為重送。
- 比較仍遵守觀察資產與fresh decision的可知時間門檻，未來請求不提前改早期numeric prefix。這不是一般非同步收件API；未送達流程者不假定已核驗。
- 對已知ID，order_history只用於尋找歷史單身分、核對exact retry。未知ID引用歷史舊單仍拒絕；不得復活已取消舊單，或把舊取消清單套到新帳。
- request_content_id與attempt_id不同：前者綁提交內容，後者繼續綁observed_at／outcome／decision／source。跨觀察相同重送不因處理時間不同而誤判內容碰撞。
- checkpoint核原request指紋、request的ID／order／plan／checkpoint／取消清單／decision綁定及fact_source原宣告一致；沿既有latest、原帳opening／權利／fills／reserve／完整token鏈。保留receipt不等於來源被認證。
- decision/execution/comparison為0.8，checkpoint為0.7；fact-history0.3與fact-receipt0.1不變。舊READ原樣，不重算、不推造舊request指紋、不隱式遷移。
- 碰撞actual為ERROR、execution=null，代表純模擬在該處拒絕；不當作成功execution的零成交或完成撤單。衝突前合法輸入／checkpoint另存，不撤銷歷史合法結果、不重設資本。

明示六案例及正反例見REPORT／before／after-final。來源更正、通用認證、完整分叉與未支援帳務不在此契約；全部外部資格false、主壓力null與原來源拒算保持。
