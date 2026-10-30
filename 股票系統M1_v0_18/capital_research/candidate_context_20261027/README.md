# 獨立數量候選入口數值環境隔離0.2.1

直接呼叫 `quantity_candidates.generate` 時，現在使用明示的內部 Decimal 環境，不繼承呼叫端的指數範圍、traps、flags 或捨入設定。只修環境隔離，候選、成本、風險、資格及帳務公式不變；輸入／輸出 schema 0.1／0.2 不變，舊保存結果不重算。

修前兩份保存請求在狹窄指數範圍下都出現 `Overflow`；正常、向上／向下捨入及 Inexact trap 控制則都與原件相符，不能冒稱這些控制也重現缺陷。修後兩份請求各五組設定，完整結果及身分全部等於既有原件，呼叫端與輸入不變。

- [契約](CONTRACT.md)、[結果與限制](REPORT.md)、[精確輸入來源](input.json)、[事前預期](expected.json)。
- [修前結果](before/summary.json)、[修後結果](after/summary.json)、[修前 source](before/source/quantity_candidates.py)。每筆 actual 綁原件完整 SHA 與確切輪次，不只比較摘要。
- [候選／原帳／權利／前身／token](test-evidence/candidates-and-binding.json)：全換仍等待交割重評；舊觸發新增 B 仍拒絕，不把其他持股 C2 當已清倉。
- [fresh 程序](test-evidence/fresh-process.json)、[呼叫端狀態](test-evidence/preset-state.json)、[搜尋上限拒絕](test-evidence/search-limit.json)。沒有新委託、成交或回放。
- [首次五方法紀錄](tests.log)、[僅補失敗方法](tests-final-binding.log)、[斷言診斷](diagnostics/current-versus-origin.json)。最終五個唯一方法通過，共六次方法執行；不累加前後控制或歷史 PASS。

首次測試把第二輪當期估值 2226.660 誤當原始本金 2230。失敗 log／測試 source 留史，只修測試：當期估值對照未改的保存 generation，原始本金另核 checkpoint。沒有改 oracle、production 或原件來迎合斷言。

這是合成工程機制，不證市場績效或策略優劣。1101 期初 cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、正式資格 false／主壓力 null 及原未支援保持。無人工操作；策略觸發、期間、風險／資金與分批規則仍由 Work 與使用者決定。
