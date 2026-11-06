# 先完成Codex可獨立處理的部分：評估器數值穩定性

同一份帳務，不應因另一個程式的數值設定不同，就換一個答案或突然中斷。本輪已修好這個問題，沒有新增READ／並列工具、策略或行情。

## 實際證據

- [修前摘要](before/summary.json)及[另一捨入方向](before/summary-extra.json)：正常及ROUND_UP對此輸入相符；ROUND_DOWN不同，開啟Inexact陷阱或縮小指數範圍會拋出Inexact／Overflow。沒有把相符的控制組算成失敗。
- [修後摘要](after/summary.json)及[追加控制](after/summary-extra.json)：五組均與原正常結果完整相同，包含evaluation_id；呼叫端設定與輸入均不變。
- [必要測試](tests.log)：5個唯一方法首次通過，含未知拒算、既有評估步驟、跨程序DefaultContext修改及禁回放／寫檔／網路。
- [整體進度與本輪界線](REPORT.md)、[契約](CONTRACT.md)、[精確輸入](input.json)、[差異短摘](diagnostic-differences.json)。修前source保存在[原碼快照](before/source/account_metrics.py)，未覆寫。

修復只在account_metrics.evaluate_saved內建立明確的50位數值Context，不繼承呼叫端捨入、陷阱、flags或指數限制，也不改呼叫端。implementation revision為0.1.1；輸入／輸出schema仍0.1，正常舊結果／數值／簽章完整相符。回撤、成本、權利等公式都未變。其他引擎的數值Context不在本輪修復範圍。

## 使用方式保持

原全帳戶評估API與`account_metrics_read`明示評估入口直接沿用修復；既有`evaluated_replay`新RUN的評估步驟亦沿用。舊READ仍只讀保存結果，不重算或修正歷史紀錄；舊的異常環境輸出留史，不能拿新source重算後冒充舊結果。

普通使用者不需修改環境、搬檔或重跑命令。這次沒有新回放、成交、帳務重建、舊suite、UI／Android或樣本外；不是市場績效。1101權利UNKNOWN、70／2／其中8／真實總淨合格0、全部正式false／主壓力null保持。
