# 回放入口不再受呼叫端數值設定影響

同一份明示合成回放，原本可能因呼叫端的捨入設定而改變報酬尾數／保存身分，或因數值陷阱直接中斷。本輪只修公開入口的數值環境；帳務、風險、資格與觸發公式沒有改。

## 已保存的實際證據

- [精確輸入與預期](cases/complete/)及[五組環境](contexts.json)，都先於執行凍結。
- [修前摘要](before/summary.json)：正常及ROUND_DOWN相符；ROUND_UP有差異，Inexact／Overflow兩項例外。
- [修後摘要](after/summary.json)：五組完整結果都等於修前正常控制，輸入與呼叫端Context保持。
- [逐輪原帳核對](test-evidence/account-chain.json)：三筆合成成交、首輪A80/B7/C2、終點A90/B8/C2；原A10及現金80權利各到位一次，原資本2230及reserve100、latest／全部token保留。
- [舊觸發仍拒絕](test-evidence/old-trigger/)及[5個唯一方法測試](tests.log)。沒有把前後批次或環境數累加成PASS數或市場樣本。
- [範圍及自審](REPORT.md)、[契約](CONTRACT.md)、[修前原碼](before/source/quantity_replay.py)。

`objects/`是內容定址的完整原始JSON：相同輸出只存一次，before／after引用同一內容不代表沒執行；每筆actual仍記本次source版本。修前ROUND_UP不同原件也完整保留，沒有覆寫。這些只屬本輪明示合成診斷，不是舊producer的新驗收或市場績效。

## 使用方式與限制

`quantity_replay.replay_sequence(request)`及既有外部協調器照原方式呼叫，現在在入口固定原標準50位／ROUND_HALF_EVEN等完整local Context。implementation revision0.1.1；輸入／輸出schema0.1及正常全文／簽章不變。舊READ不重算或隱式修正歷史原件；舊manifest對照其歷史source，不要求現在source等於舊版。

仍須明示選擇與委託，無自動比例、門檻、建單或策略勝者。真實權利、來源認證、外部活單／期初應付／信用、R2/F及其他原未支援保持。只保護經此回放入口的呼叫；直接繞過入口呼叫其他模組尚未驗證。本輪不增加READ工具、行情或回放能力。

1101期初cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、正式false／主壓力null保持。使用者無需人工操作，無需Work重做工程驗收。
