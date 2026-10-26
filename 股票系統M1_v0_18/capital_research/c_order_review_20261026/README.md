# C類原條件單同單重評：閱讀入口

本輪基線 `5be3d8bea1008361642b3ec3a6bfdafaa16373a9`。只補同一已核准C買單的重評，不增加新批、不選比例；所有數字皆合成。

- [完整結果與界線](REPORT.md)、[事前契約](CONTRACT.md)。
- [最終14案索引](after-checkpoint-fix/summary.json)、[合法原單](after-checkpoint-fix/valid-C-same-order/actual.json)、[部分7股後撤銷剩13股](after-checkpoint-fix/future-revocation-known-after-partial/actual.json)。
- [原單白話摘要](readback/valid-C-same-order.txt)、[部分成交後撤銷摘要](readback/future-revocation-known-after-partial.txt)。READ只投影保存結果，不重算。
- [7個作用域拒絕案例](gateway/summary.json)、[下一批新舊觸發對照](new-batch-final/summary.json)。下一批只驗資格，未建單或成交。
- [首批13方法的失敗診斷](tests-final.log)、[修正後5個相依方法](tests-after-checkpoint-fix.log)、[自審](self-review.json)、[檔案清單與指紋](CHANGE_MANIFEST.json)。不把兩批算成18個唯一方法。

`before/`是原版行為；`initial/`、`after-final/`、`new-batch/`和對應log為中途歷史，包含checkpoint版本指紋錯誤，不作本次交付結果。最終只看`after-checkpoint-fix/`及`new-batch-final/`；原斷言、舊證據未覆寫。`gateway/`使用尚未升版的0.8／0.7原單prefix，不受新0.8 checkpoint指紋修正影響。

唯一公開數值入口仍為 `conditional_quantity_review.reassess_conditional(request)`。選用 `capital-conditional-quantity-review-input/0.2` 才啟用C原單；原0.1仍維持B/E。不能把本資料當成正式買進批准。
