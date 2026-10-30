# 公司行動與逐日資金帳候選 0.1（最新交付）

**工程已實作／測試；真實總淨報酬比較仍無合格窗口。**

閱讀 [實測與缺口](REPORT.md)、[精確契約](CONTRACT.md)、[完整接續指令](WORK_HANDOFF.md)。下載ZIP與SHA：根目錄 `deliveries/m1-actions-ledger-20261022/README.md`。原P1-7報告／ZIP／18測試9982核對保持為歷史。

- 真實事件：`events.json`（4官方原件、四現金＋一配股組件，完整來源定位）；不是完整覆蓋。
- 資格：`window-qualification.json`（70拒算＋2不足，總淨報酬／排名null）；`real-input-probe.json`／`real-input-refusal.json`可重現。
- 可讀逐日帳：`engineered-daily-ledger.csv`、`engineered-examples.json`（三個**工程測試**案例）。真實毛時程 `gross-schedule-preview.json` 不提供淨現金、實際到款或報酬。
- 證據：`tests.log`（本輪44通過）、`study-verification.json`、`cli-verification.json`、`bootstrap.log`、`preservation-audit.json`與來源節點讀回收據。

查看GitHub Markdown／JSON／CSV不需安裝；執行命令見REPORT。沒有新增UI，無需再做同版手機按鈕驗收。手機／瀏覽器未測；不以工程情境當作真實行情或投資成績。

以下保留來源完成節點說明，其「後續待實作」已由上方新交付接續：

---

# 公司行動原件事件表 0.1（2026-10-22）

獨立候選，來源輸入提交354a9c01；不更改P1-7的原價格報酬。
`events.json`從四份已存官方原件產生五個事件組件（四現金、一配股），逐欄保留URL、SHA256、擷取時間、列欄定位及原值。基準日、除權息交易日、發放日分存；公布時間仍未知。

2884的2025股票股利0.10015129是每股金額，不是股份比率；無可核面額／直接配股比例、上市可交易日與零股處理，不換算。配股發放日不冒稱可交易日。完整減資／其他行動覆蓋未驗，2026交易所原件只至7/24，7/25～10/16缺口明示。四筆現金股利有公司預定發放日，沒有投資人淨入帳／扣款證據。

本節點6個來源測試通過。純數值資金帳及合格窗檢查仍待本輪後續節點，不以事件表完成代表總淨報酬已完成。

重現（專案目錄）：`python3 -m rotation_research.action_sources`；`python3 -m unittest rotation_research.test_action_sources -v`。

`fetch-attempt.json`記錄本環境一次官方會議紀錄請求：代理Tunnel 403，沒有繞過，也沒有重試舊除權端點。原件解析初次碰到表頭而拒絕；已以日期格式篩掉表頭後重跑成功。這不是行情或事件值修補。
