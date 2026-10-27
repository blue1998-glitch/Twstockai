# C原單重評與一次再評：外層數值環境隔離

兩個既有公開入口現在保護完整呼叫：`reassess_conditional` revision0.2.1、`retry_rejected` revision0.3.1。只固定數值環境，沒有改原單、remaining、family／觸發、帳務、策略或資格；review schema0.1／0.2／0.3及decision／execution0.9、checkpoint0.8保持，舊READ不重算。

先重現，再分步確認：修前重評有Overflow，再評有Overflow／Inexact；只修重評後，再評仍在自己的checkpoint核對失敗，因此才修第二入口。兩個本體原樣保留。修後十組完整主結果及十二組必要邊界結果全部等於原保存actual，來源與oracle沒有改。

- [事前契約](CONTRACT.md)、[精確input／expected／actual來源](input.json)、[凍結預期](expected.json)、[報告](REPORT.md)。
- [修前主結果](before/primary/summary.json)、[只修重評的中間版本](after-review-only/primary/summary.json)、[最終主結果](after/primary/summary.json)、[必要邊界結果](after/regressions/summary.json)。每筆有完整stack／兩份source指紋／輸入及caller前後狀態；相同大結果精確引用固定原件。
- [原單／資本／權利／reserve／latest及token](test-evidence/order-and-account.json)、[UNKNOWN／部分成交／取消／到期／錯身分](test-evidence/selected-boundaries.json)。
- [preset保持](test-evidence/preset.json)、[兩入口fresh程序](test-evidence/fresh/summary.json)、[既有READ相容](test-evidence/READ-compatibility.json)、[六唯一方法首次通過](tests.log)。不累加舊PASS、控制、子程序或案例。
- [自審／執行](execution.json)、[原件保全](preservation.json)、[提交指紋](CHANGE_MANIFEST.json)。before與after-review-only留史，after才綁最終source。

原資本1430、reserve100、原r1-B買單剩餘20及B-event觸發保持，不變新批。再評保留第一次REJECTED receipt再加當期ACCEPTED；UNKNOWN仍不買，部分7股後13股取消／到期，錯原單或前身仍停止。新批仍須獨立觸發，未新增批次委託或1/13行情。

入口內有既定原核准重建：每個主例皆含一次quantity回放／生成，重評simulate2次、ledger34次，再評simulate3次、ledger66次；不是無引擎READ，也不另跑舊suite或producer。fresh禁止保存／寫檔／網路，輸入、caller及DefaultContext保持。既有lifecycle READ則明確禁所有引擎，仍READABLE且全文相符。

無人工操作；只證合成機制。1101 UNKNOWN、70／2／其中8／真實總淨合格0、正式false／主壓力null及原未支援保持，不證策略或市場績效。下一步可留Codex，只收斂剩餘獨立入口是否影響現行明示研究流程，沒有實際缺口就停止同類修補；策略仍由Work與使用者決定。
