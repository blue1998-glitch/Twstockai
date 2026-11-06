# 完整明示行動的全帳戶評估轉接 0.1

現在可從完整保存的 HOLD／現金買進／減碼／退出結果，沿同一本原帳評估成長、最大回撤與恢復時間。部分成交後若另有同原單的完整續播保存結果，也可一起核對。只讀原件並計算新評估，不重播帳務、改權利、建單、排名或提升資格。

## 入口

`capital_research.action_account_metrics.evaluate_saved(request)` 是純數值／保存結構校驗入口。輸入 `capital-action-account-metrics-input/0.1`：

```json
{"schema":"capital-action-account-metrics-input/0.1","synthetic":true,"evaluation_at":"2026-01-12T16:00:00+08:00","saved_result":{"schema":"capital-saved-action-source/0.1","action_request":"完整原執行請求（此處為說明）","action_result":"完整原保存結果（此處為說明）","continuation":null}}
```

完整實際請求見 [退出例](cases/exit-B7/input.json) 與 [部分成交續播完成例](cases/continued-partial/input.json)。欄位是完整物件，不接受上述說明字串、單一numeric_result、ledger或checkpoint摘要。來源須明示，不自動選最新結果。`continuation` 限 null 或一份 exact request／result；不是任意外部單或多段協調器。

沿既有 `account_metrics_read` 增加明示來源種類，預設 `quantity` 不變。例如在 `股票系統M1_v0_18` 目錄：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m capital_research.account_metrics_read --source-kind action --source capital_research/action_metrics_20261029/validation-corrected/controls/cli/source.json --evaluation-at 2026-01-12T16:00:00+08:00 --format text
```

這是讀保存帳、計算新評估並輸出stdout；不改原件、不重播、不覆寫保存評估。JSON沿用 `--format json`；此里程碑沒有新增自動RUN／儲存協調器。保存actual直接閱讀即可，無須再跑指令以取得相同結果。

## 合成案例的白話結果

各路為互斥研究分支；不加總共享持股／現金、不排名。原始資本1180、一般預留100、現金／股份權利及歷史token保留。完整原曲線只有1/5～1/12八列，不能宣稱已驗長期績效。

| 明示行動 | 期末原帳應計淨值 | 期間成長／最大回撤的手算分數 | 恢復 |
| --- | --- | --- | --- |
| 減B3 | 1176.80 | -3.20 / 1180 | 截至1/12未恢復，峰日至終點7日 |
| 退出可賣B7 | 1176.72 | -3.28 / 1180 | 同上 |
| B7拆3＋4 | 1174.72 | -5.28 / 1180 | 同上；原逐fill費稅較多 |
| B20退出意圖只成7，剩13續播到期 | 1176.46 | -3.54 / 1180 | 同上；不冒稱已退出20 |

成長、回撤與恢復沿原 `account_metrics` 公式，不另寫財務公式。已記錄費稅已在曲線內，不再扣；期末假想退出成本及成本後成長保留原帳數字另列，不當作實際已清倉或每日可賣。未恢復保留 null／截尾，不補恢復日。

## 證據與版本

- [事前契約](CONTRACT.md)、[凍結指紋](frozen.json)、[原件來源及保護清單](intake.json)、[29組精確input／expected](case-index.json)。
- **最終actual是 `final-corrected/`**：[總表](final-corrected/summary.json)、[退出評估](final-corrected/exit-B7/actual.json)、[續播完成評估](final-corrected/continued-partial/actual.json)、[source版本](final-corrected/source-versions.json)。
- `initial/`、`after-final/`、`final/` 均為中間版本，原樣留史；不可把其source指紋當現行source。舊quantity及原0.1／0.2行動結果不改。
- [最終8唯一方法log](tests-corrected.log)、[獨立手算](validation-corrected/test-evidence/manual-check.json)、[原帳／權利／latest／token](validation-corrected/test-evidence/continuous-book.json)。
- [完整Context控制](validation-corrected/controls/context/actual.json)、[fresh process禁引擎／IO／網路](validation-corrected/controls/fresh/actual.json)、[舊quantity完整結果](validation-corrected/controls/legacy/summary.json)、[明示CLI輸出](validation-corrected/controls/cli/actual.json)。
- 自審發現並修復兩項新轉接漏檢：[續播原close來源](diagnostics/resume-close-binding/)、[衍生資料與原事實來源](diagnostics/derived-source-binding/)。各自先存精確input／expected／修前actual；`corrected-actual.json`才是最終反例結果。
- `tests-reviewed.log` 保存一次錯誤碼不一致的失敗；未改oracle，統一對外拒絕碼後通過。三批測試只算 **8個唯一方法**，不累加為24，不加歷史PASS或29案例。
- [詳細報告](REPORT.md)、`preservation.json`、`CHANGE_MANIFEST.json`。manifest不含自身，保存前才建立。

## 限制

1/9部分結果有待交股份，原ledger.status仍是PARTIAL_LEDGER_RETURN_REFUSED，評估REFUSED／statistics=null；1/12完整續播結果才可評估。早於close.available_at、缺價／缺日／未知權利、改原帳／latest／token／預留或來源錯配亦拒絕。不利用無記錄推定無成交，不回填行情或權利。

這是保存結構、來源連結與原曲線一致性校驗；不是來源認證、逐分錄獨立審計或策略重評。不能識別所有自洽造假。只支持完整明示合成原窗與一份精確相連續播；不擴多段來源矩陣、R2/F、信用、未知期初款、真實市場回放或策略。所有正式資格false／主壓力null、70／2／其中8／真實合格0、1101 UNKNOWN、來源parents／圖形人工及未讀原件限制保持。

原唯一Codex依里程碑自審、原分支正常保存及GitHub固定SHA讀回，無需人工搬檔或Work例行驗收。若接續，先核既有保存流程能否直接另存評估，不重建協調器；買賣規則與市場來源仍須另行研究。
