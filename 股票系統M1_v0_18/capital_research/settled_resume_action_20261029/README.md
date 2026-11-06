# 續播結清後，直接接既有明示行動

本輪已用保存原件完成「原單部分成交 → 續播交割／到期 → 明示下一項行動」的接續驗證。**不需要新增轉接層；產品程式改動0。** 只使用現有 `cash_action.evaluate` 與 `cash_action_execution.execute`，不產生策略、股數或新行情。

1/8原單已成交B7、剩13到期，現金858.86、一般預留100；另有現金權利80及C2股份權利。完整原帳、前身與9個歷史token直接承接。

| 明示合成分支 | 結果 | 入口 |
|---|---|---|
| 續抱 | 無新成交；1/12現金938.86，B7/C4 | [actual](actual/hold/result.json) |
| 新獨立觸發B20 | 只新單成交20；1/12現金537.46，B27/C4 | [actual](actual/independent-B20/result.json) |
| 舊觸發／假首次／預留不足／錯前身／仍有活單 | 五個反例都在simulate前停止 | [總表](summary.json) |

這兩個正例是互斥研究分支，不可加總部位，也沒有比較策略優劣。B20沿已存明示研究參數；B40僅為資金預留邊界診斷，不是使用者交易數量或規則。

- [REPORT：逐日帳務與限制](REPORT.md)
- [CONTRACT：事前凍結範圍及預期](CONTRACT.md)
- [原checkpoint與來源綁定](original-binding.json)
- [逐日手算與核對](test-evidence/daily-handcheck.json)
- [前身／原單／權利／全部token核對](test-evidence/chain.json)
- [4個必要測試方法](tests-final.log)
- [保存及自審證據](preservation.json)

原續播結果只READ，沒有重跑原委託；僅兩項新行動各呼叫原simulate一次。原窗口仍止1/12，tape／日曆不變。source、費稅、帳務、決策、正式資格及拒算均不改；全部正式false／主壓力null保持。真實帳戶資料缺口、未知期初權利及市場策略尚未解除。

數值環境與未來隔離證據沿未改產品source重用，本輪未新增完整未來／分叉矩陣。既有1/12主例已到窗口末端，不能因此補1/13行情或宣稱後續可成交。
