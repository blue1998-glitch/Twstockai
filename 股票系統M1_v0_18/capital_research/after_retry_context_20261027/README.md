# 完成原單重評後接回候選：外層數值環境隔離0.1.1

現在 `quantity_after_retry.generate_after_retry` 的完整呼叫都使用明示的內部 Decimal 環境，連進入候選產生器前的 checkpoint 核對及原帳導出也受保護。只改這個外層環境，沒有改帳務、候選、資格、策略或原結果；原 schema0.1 保持，舊READ不重算。

三個主例是既有新獨立觸發、舊觸發及資格UNKNOWN。修前各有 Inexact 與 Overflow 中斷，正常與兩種捨入控制完整相符；修後十五組全文及身分均等於原保存結果。不是只看候選數量，也不能把未重現差異的捨入控制稱為缺陷。

- [事前契約](CONTRACT.md)、[精確輸入與原件指紋](input.json)、[事前預期](expected.json)、[完整報告](REPORT.md)。
- [修前](before/summary.json)／[修後](after/summary.json)；每筆 actual 精確綁完整舊原件，不複製大型原件或截斷內容。
- [Inexact 中斷位置](before/boundary/inexact-trap/actual.json)、[Overflow 中斷位置](before/boundary/narrow-exponents/actual.json)：原外層各呼叫一次，均在第一次 ledger 核對中斷，內層 generate 尚未呼叫。
- [原帳／權利／預留／前身／token與候選](test-evidence/account-and-candidates.json)、[必要拒絕反例](test-evidence/refusals.json)、[呼叫端狀態](test-evidence/preset.json)、[fresh 程序](test-evidence/fresh-process.json)。
- [本輪五唯一方法紀錄](tests.log)、[自審及執行](execution.json)、[原件保全](preservation.json)、[提交範圍指紋](CHANGE_MANIFEST.json)。五方法首次通過，不累加歷史PASS、控制或子程序。

原資本1430與當期估值1425.100分開；A60/B25/C2、現金275.100、一般reserve100、完整原帳／fills／權利／未成交歷史、latest與12個歷史token保持。新觸發仍須完整候選檢查；舊觸發及UNKNOWN不得加碼，全換仍等待交割重評。沒有建單或新增成交。

所有結果只證合成工程。1101 cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、正式資格false／主壓力null及原未支援不變。無人工操作，不預設轉Work驗收；未定策略仍由Work與使用者決定。
