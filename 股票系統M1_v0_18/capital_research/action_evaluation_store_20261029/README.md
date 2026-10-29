# 既有行動評估的明示匯入保存 0.1

完整來源與已完成評估現在可一起不可覆寫保存，之後純READ取回。重用原Journal與保存讀回，不再計算成長／回撤／恢復，也不回放交易或帳務。保存成功與評估資格分開；REFUSED可以留存，仍是拒算。

## 使用

- `capital_research.action_evaluation_store.import_evaluation(root,id,request)`：明示匯入，保存並讀回。
- `read_evaluation(root,id)`：只接受保存位置及ID，不收新input、不重新評估。
- 完整請求見 [退出例](cases/exit-B7/input.json)、[部分續播完成例](cases/continued-partial/input.json)、[拒算留存例](cases/partial-prefix/input.json)。必須包含完整原evaluation_input／evaluation，另明示兩者expected ID，不能用摘要或自動挑最新來源。

在`股票系統M1_v0_18`目錄，可直接讀本輪已保存原件，不必重跑IMPORT：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m capital_research.action_evaluation_store_cli READ --root capital_research/action_evaluation_store_20261029/actual/records --id exit-B7
```

新增獨立研究紀錄時才使用明示IMPORT（既有ID不覆寫）：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m capital_research.action_evaluation_store_cli IMPORT --root /tmp/twstock-action-evaluation-example --id explicit-example --input capital_research/action_evaluation_store_20261029/cases/exit-B7/input.json
```

CLI輸出JSON receipt。`storage_status`與`evaluation_status`分開：SAVED_AND_READ_BACK／READ_ONLY不等資料、交易或策略合格。全部正式flags仍false、primary_pressure_id=null。沒有RUN或自動評估、來源選擇、重試／修復入口。

## 保存及讀取界線

每ID是一份原Journal `rotation-record/0.1`，value為新版`capital-action-evaluation-record/0.1`，包含完整import_input與來源／input／evaluation／record指紋、原截止與資格。單筆保存不另設四階段協調器。同ID同內容重送不更動bytes／mtime；不同內容NOT_SAVED，原件保留。

寫入或讀回不確定為UNKNOWN，不當成功；原件及部分檔保留，使用者／外層只能明示READ核對。READ缺檔NOT_FOUND，損壞、跨來源、錯schema／指紋UNREADABLE，不重算或補檔。單程序及既有Journal能力範圍，不宣稱多程序exactly-once或真實斷電耐久已全面驗證。

EVALUATED來源沿既有純來源校驗、原帳／權利／reserve／latest／全部token、原截止／可得時間、原成本／期末值及逐日equity精確比對。七個校驗函式從原action_account_metrics原樣搬到saved_action_source，原數值API函式文字與數值公式未改。IMPORT／READ不載入評估器。

REFUSED舊評估沒有producer input attestation且source=null，因此只保存外部明示的pinned input與拒算原件配對，標記 **EXPLICIT_REFUSAL_ASSOCIATION_NOT_REEVALUATED**；不稱已重新驗證拒算原因來自該input。拒算來源仍須完整明示合成輸入，所有指標／帳／來源／成本為null。缺完整來源、錯外部ID、REFUSED夾指標或正式資格true都不保存。

這是保存結構／來源連結校驗，不重新認證來源、每筆分錄或指標公式；不能識別所有自洽重新簽名的數值改寫。正式來源／策略許可與未知證明仍由原機制決定，不能靠存檔升格。

## 證據

- [事前契約](CONTRACT.md)、[精確input／expected清單](case-index.json)、[來源及保護指紋](intake.json)、[凍結指紋](frozen.json)。
- [16組IMPORT／READ總表](actual/summary.json)、[真實保存檔案](actual/records/)、[退出匯入receipt](actual/exit-B7/import.json)、[純READ receipt](actual/exit-B7/read.json)。此處「真實保存」只指確實寫檔，資料仍為合成研究。
- [8唯一方法log](tests.log)、[測試程式](test_store.py)、[原payload／權利／token](validation/payload-preservation.json)、[純函式搬移對照](validation/pure-move-regression.json)。
- [相同／衝突ID與symlink](validation/identity-controls.json)、[寫前／寫後／讀回及部分檔故障](validation/storage-faults.json)、[READ損壞／跨來源拒絕](validation/read-rejections.json)。故障只用新暫存副本，不接觸舊紀錄。
- [新程序CLI禁producer／評估器與READ寫入](validation/fresh/summary.json)、[完整Context及input不變](validation/context-controls.json)。新評估、決策、回放與帳務producer呼叫均0。
- [報告](REPORT.md)、`preservation.json`及`CHANGE_MANIFEST.json`。manifest不含自身；原來源／oracle／actual與歷史log不覆寫。

## 保持限制

只支持既有完整明示合成行動評估及至多一份相連續播的來源，沒有市場回放、策略、排名、來源認證或自動協調器。1101期初cash_claims UNKNOWN、70／2／其中8／真實合格0、正式false／主壓力null、全部parents、圖形人工及原未支援保持。Work／Astra／第一工作區救援原件未讀，不宣稱Work驗收。

由原唯一Codex自審、正常保存及GitHub固定SHA讀回，無人工搬檔或例行Work工程驗收需求。本項結清後不再添加相同保存／READ包裝；下一步依既有優先順序，未定買賣規則、期間、比例與市場來源仍由Work與使用者研究。

提交前staged格式檢查攔下saved_action_source.py尾端多餘空白；只移除空白，函式逐字相同，未重跑測試。actual/source-versions.json保留測試時版本；final-source-versions.json為提交版本，diagnostics保存差異及修前manifest／preservation。輸入、預期、actual及log均不改。

格式修正後的來源指紋方法單獨重驗，見tests-format-corrected.log；tests-format.log的舊指紋失敗保留。仍只計8個唯一方法，不累加重驗。
