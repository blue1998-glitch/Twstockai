# 直接決策及完整續接數值環境隔離0.9.1

`core.decide` 與 `resume_decision` 現在都使用明示的內部 Decimal 環境；續接保護涵蓋前身及原帳checkpoint核對，不只最後的數值決策。只改入口環境，原續接本體機械移至私有helper，計算、權利、資格及策略不變。原decision schema0.8／同單0.9保持，舊READ不重算。

直接取已保存回放兩輪的原決策參數，不重播市場。預期decision取原execution保存欄位，metadata按原契約綁原輸入／checkpoint；不是用新RUN填oracle，也不冒稱舊原件另存完整wrapper。

- [事前契約](CONTRACT.md)、[精確輸入來源與指紋](input.json)、[事前預期](expected.json)、[五項拒絕規格](regression-specs.json)、[完整報告](REPORT.md)。
- [修前](before/summary.json)／[修後](after/summary.json)：修前僅兩個狹窄指數控制重現Overflow，其餘八組完整相符。續接在bind_resume核帳中斷，內部_decide呼叫0；修後十組完整相符。
- [修前拒絕診斷](before/regressions/summary.json)／[修後拒絕](after/regressions/summary.json)：正常拒絕保持；修前四個preset被Clamped遮蔽，修後均回到預期ValueError，從未因此變成合格或成交。
- [原帳／權利／前身／全部token](test-evidence/account-and-history.json)、[preset與輸入保持](test-evidence/preset.json)、[兩入口fresh程序](test-evidence/fresh/summary.json)、[既有候選相依整合](test-evidence/quantity-integration.json)。
- [六唯一方法本輪首次通過](tests.log)、[自審／執行](execution.json)、[保全](preservation.json)、[完整提交指紋](CHANGE_MANIFEST.json)。前後控制、子程序與歷史PASS不累加。

原本金2230與續接當期估值2226.660分開，現金1056.660／reserve100／A80/B7/C2、現金80與A10權利保持；原兩筆部分成交與剩餘A30／B13到期狀態不變，沒有復活舊單。latest及9個原token承接到12個當期reviewed token，未重設資本或另建帳。

無人工操作。所有結果僅證合成工程，正式資格false／主壓力null、1101 UNKNOWN與70／2／其中8／真實總淨合格0及原未支援保持。不宣稱其他直接成交／重評／帳務入口已全面隔離，也未重跑完整同單0.9矩陣。策略問題仍由Work與使用者決定。
