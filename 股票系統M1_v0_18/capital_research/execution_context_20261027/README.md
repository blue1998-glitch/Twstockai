# 直接execution.simulate外層數值環境隔離0.9.1

直接呼叫 `execution.simulate` 現在使用明示的完整 Decimal 環境，保護範圍包含決策返回後的預留、風險、成交與原ledger核對。只改公開入口環境，沒有改成交條件、帳務公式、策略或資格；execution schema0.8／同單0.9保持，舊READ不重算。

原保存兩個job直接重用，不執行quantity回放producer。修前兩例各重現Inexact及Overflow；續接ROUND_UP另改變scenario_net_return尾數與result_id，成交／現金／持股不變。其餘五組控制相符。修後十組完整execution及身分全部等於原件。

- [事前契約](CONTRACT.md)、[精確job／actual來源](input.json)、[事前預期](expected.json)、[三項拒絕規格](regression-specs.json)、[報告](REPORT.md)。
- [修前](before/summary.json)／[修後](after/summary.json)、[ROUND_UP完整差異路徑](before/round-up-difference.json)。修前例外stack逐筆留存，證明在決策返回後的原ledger核對中斷。
- [逐日帳／成交／交割／權利／預留／前身與token](test-evidence/account-chain.json)、[原checkpoint相容](test-evidence/checkpoint-compatibility.json)、[三項拒絕修後](after/regressions/summary.json)。
- [preset與輸入保持](test-evidence/preset.json)、[兩個fresh程序](test-evidence/fresh/summary.json)、[六唯一方法首次通過](tests.log)。不加舊PASS、前後控制或子程序。
- [保全](preservation.json)、[自審／執行](execution.json)、[提交指紋](CHANGE_MANIFEST.json)。差異完整JSON在objects，相同結果直接精確引用舊原件，不截斷或覆寫歷史。

原本金2230／reserve100保持；首輪A20／B7部分成交，A30／B13餘量到期，後輪只有原核准B1。現金80與A10權利各到位一次，終點現金1115.640、A90/B8/C2、應計2225.640與原件一致；不是只靠終點相等，還核逐日prefix、journal及原單歷史。首輪未完結的ledger仍沒有end_net_equity／費用彙總，scenario_net_return仍null；未補零或冒合格總淨報酬。

無人工操作。只有合成診斷，非市場績效或策略批准；1101 UNKNOWN、70／2／其中8／真實總淨合格0、正式false／主壓力null及原未支援保持。其餘獨立原單重評／全換／帳務入口不宣稱全面隔離，未重跑同單0.9完整矩陣。未定策略仍由Work與使用者決定。
