# M-G3｜核心0.2互動研究主圖

[完整新版HTML](../output/mg3_20261101/M1_v019_graph_recognition_v02.html) · [工程報告](REPORT.md) · [固定案例actual](actual.json) · [精簡驗收結果／來源指紋](verification.json) · [Chromium報告](browser-first/browser-report.json)

這是單檔研究圖表成品，不是已部署網站。GitHub程式碼頁不會執行HTML；可用「Download raw file」取得**該單一HTML成品**後，由可開啟本機HTML的瀏覽器檢視，無需終端機、來源ZIP或安裝工程環境。本輪只驗127.0.0.1臨時HTTP的Chromium；未重新嘗試環境曾拒絕的file://，未驗Android實機或手機檔案開啟流程。若裝置／平台不提供HTML開啟，應維持「成品可用、手機實際使用未驗收」，不能稱已部署。

## 操作

1. 選股、選「已算分析日」。日K、量、MACD及查詢保留全部原始紀錄；回放僅播放已預算日期，不在網頁補算。
2. 選研究箱 →「數值與反證」。向下捲證據面板閱讀A形成來源、B形成後觀察、C歷史脈絡；各資料表可橫向捲動，長表在內部捲動。
3. 「整個研究箱」與「研究壓力帶」是兩種不同位置；例如1101在2025-05-14對L3是箱內，但低於壓力帶。
4. 「聚焦來源」、形成後聚焦及事件按鈕只移動圖／游標，不改分析日期。返回24月可回主圖。候選勾選只改顯示；跨缺口的歷史區域仍可定位，不延伸為現價壓力。
5. 「下載精確JSON」保留完整前綴K棒、MACD／MA原字串、原ID、確認時間、來源輸入指紋、三層證據與null。畫面約數不修改下載值。

## 固定案例入口

| 股票／分析日 | 可核內容 |
| --- | --- |
| 1101／2025-05-14、05-27 | 原L3/L6形成4/8～5/13共25筆；5/14無L6，5/27已確認。L3 id／L6 id見expected.json。 |
| 1101／2025-06-02、06-03 | 6/2首次跌出，6/3仍保留反證；原研究區域不刪除。 |
| 1101／2026-10-12～16 | 原五日參照事件順序；僅10/16另有預設折疊人工事後對照。39筆4/7～6/2與自動25筆分離。 |
| 2884／2026-07-01、21、22 | 7/1原官方X不比價註記，事件類型UNKNOWN；舊箱及高點停止比較、相對距離null。 |
| 6488／2022-09-08 | 既有跌破後回箱，原首次跌破仍在；不等正式恢復。 |
| 8069／2022-03-16 | 同上；保留原股數口徑及歷史精度限制，未認證FinMind精確股數。 |

原0.1成品、原核心與509份來源／歷史成品逐檔保全。四股原價量、MACD／MA不變；唯一輸入邊界補正是新0.2 adapter明示2884原父檔漏列的7/1不比價警告，不改原父檔或事件種類。Work G6/G12/S3顯示別名對照未取得，不猜別名；已逐值核全部原1101 IDs／幾何／父子及後繼。

## 工程重現（給Codex）

沿用現有Python／Chromium／Playwright，不bootstrap或下載來源。於專案子目錄執行；新產物目錄不得覆寫既存成品：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m graph_core_chart.build --source-spec graph_core_chart/mg3_20261101/source-input-spec.json --output-dir graph_core_chart/output/new-mg3
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest graph_core_chart.mg3_20261101.test_mg3 -v
M1_GRAPH_DIR="$PWD/graph_core_chart/output/mg3_20261101" M1_GRAPH_BROWSER_OUTPUT_DIR="$PWD/graph_core_chart/output/new-browser-evidence" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node graph_core_chart/mg3_20261101/test_browser.cjs
```

本輪已完成上述驗證，不需為增加計數再跑。測試fixture路徑固定本輪成品，若另版測試須明示對應；舊0.1結果只READ，不以現行核心重算冒稱原版本。新成品用本輪builder的明示source-spec路徑，舊render_existing／verify_artifact CLI契約仍是歷史0.1入口，未宣稱已接本版。

限制：分類NOT_VALIDATED、主要壓力null、正式資格false、歷史公布時間與完整公司行動UNKNOWN。日曆缺漏列表原樣保留，供應前綴不等完整市場日曆認證；無全市場、策略、績效、UI自動交易或Android實機驗收。FinMind與M-R2本地受限原件未使用／未上傳；M-G1、M-G2 Library原件未取得／未讀。本里程碑完成即停，不自啟下一研究。
