# 嘗試關卡／量先價：獨立候選畫面接入 0.1

依 `M1_V019_ATTEMPT_CORE_HANDOFF.md` 接續提交 `45aaeecf92fabee80a4f2729328ae161e0d0203b`。新接入版本 `attempt-view-adapter/0.1`；核心仍為**未修改的** `attempt-evidence-candidate/0.1`。

## 本輪已接入

- 新獨立頁 `M1_v0_19_attempt_candidate.html`，不覆寫舊 v0.19、v0.18 頁面或資料。先勾選啟用，再明選來源及觀察時點；沒有自選最新日期、關卡或左區。
- 顯示來源檔已明選的近期高點來源日、左區上下緣／來源日及 Raw／Adjusted 模式。它們是工程例的明選輸入，不是網頁自動辨識、使用者已在本頁選區，或已證明套牢持有人。
- 各自顯示101／106的價格子條件、盤中現價關係及最新已完成日收盤關係；量比較、量先價、量價先後未知及後來跌回各自保留。
- 先呈現當時事實、支持／反面／缺證及未知，再呈現圖與完整事件。沒有交易按鈕、綜合分數、勝率百分比、強勢延續分類、自動防守上移或持倉處置。
- 重播逐筆**已提供的觀察**，並非由日OHLC生出盤中資料。日K使用來源歷史及觀察當時已給的累計OHLC；跨日保留前日已完成K，本日未完成K用虛線框。單列來源日按序顯示，未列日期未知，不補交易日。
- 日K／量共用游標，全部已提供歷史、時間放大／縮小／左右平移；觀察點圖只連接本日已提供且不晚於當時的點，按實際時間定位。連線不是逐筆路徑。僅有完成日資料時明示盤中缺少，沒有合成觀察點。
- 股數直接使用原量，不換算股／張。左區最高量是核心回傳的指定來源日最大量，來源缺量則未知。當時累計量與歷史全日最高量是指定基準比較，沒有冒充歷史等時量或全日預測。
- 原生全螢幕及明示頁內專注備援；手機單指正常上下捲動，以按鈕操作時間窗。未新增未要求的手勢分析或介面計算。

## 資料與版本邊界

`attempt_sources.json` 明列7個**假想工程來源**、28個觀察時點：原101／106案例、同日高價／總量先後未知、左區缺量、超過兩位小數價格、只有完成日線、宣告共同錨定的Adjusted例，以及大整數股數精度壓力例。原核心fixture未修改；新增變體另存 `fixtures/view_*.json`。這不是新增真實個股分析或實際盤中來源。

本接入器目前只允許 `SYNTHETIC_ENGINEERING_FIXTURE` 與 `PARTIAL_SUPPLIED_HISTORY`，明確拒絕將未認證來源標為真實行情／完整歷史。真實來源要先核對股票／來源／模式、公司行動、同錨定、參照及歷史可得時刻；本輪未做這個新階段，不由宣告升格認證。

`attempt_view.py` 是標準Python離線adapter，明確呼叫原核心；不import舊引擎、store、Streamlit，沒有SQLite／API／持倉服務。每個觀察前綴直接交給原核心，瀏覽器只渲染返回事實與已準備的來源圖形資料；座標／顏色／視窗是顯示轉換，沒有重算關卡、量先價或分析條件。

新schema：`attempt-view-sources/0.1`、`attempt-view-bundle/0.1`、`attempt-view-selection/0.1`。它們不是原核心輸入／輸出或共同 `stock-analysis/1.0` 的遷移。舊兩日失效規則與新嘗試收盤事件不互相覆寫。

## 精確下載與前綴

每個時點的下載由Python預先產生JSON文字：完整原輸入前綴、原歷史、明選參照、共同基底宣告、核心輸出、frame／前一frame／event ID、未知與原精度，以及來源圖形資料。事件只到該時點，後來觀察不會寫回舊下載文字或ID。

**瀏覽器直接下載該文字，不做JSON.parse→JSON.stringify回寫。** 因原核心允許任意大小整數來源量，此方法保留超過JavaScript安全整數範圍的原數字型別與精度。普通價格以十進位字串進位顯示兩位小數；條件採原核心原精度。圖形座標可用Number，不能用它重算分析。

整份離線bundle含完整供應觀察軸，供使用者明選歷史重播；當前畫面與下載只使用選中前綴。bundle的整檔指紋可隨新資料改變，舊時點的下載內容與核心ID不因此改變。所有事件發生時刻仍null，首次觀察與完成資料確認時間分開；不回填精確穿越時刻。

## 重現

Git checkout先在repository root跑 `python3 codex/bootstrap_m1.py --hydrate-missing`。完整離線ZIP已附資產，不需重新bootstrap。以下在 `股票系統M1_v0_18` 執行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m product_candidate.attempt_view \
  --sources product_candidate/attempt_sources.json \
  --output-dir product_candidate/output/attempt-view-v01
PYTHONDONTWRITEBYTECODE=1 python3 -m product_candidate.verify_attempt_view \
  --sources product_candidate/attempt_sources.json \
  --candidate-dir product_candidate/output/attempt-view-v01 \
  --report product_candidate/output/attempt-view-v01/source-replay-report.json
M1_ATTEMPT_DIR="$PWD/product_candidate/output/attempt-view-v01" \
M1_ATTEMPT_BROWSER_OUTPUT_DIR="$PWD/product_candidate/output/attempt-browser-v01" \
CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium \
node product_candidate/test_attempt_browser.cjs
mkdir -p product_candidate/tmp
TMPDIR="$PWD/product_candidate/tmp" PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -v
```

輸出3個不同檔案：`attempt-candidate.json`、`M1_v0_19_attempt_candidate.html`、`attempt-selection-oracle.json`。相同內容重跑回報EXISTING；任何已有不同內容／symlink會在寫新檔前拒絕，請用新輸出目錄，不覆寫歷史。多檔是防覆寫輸出，並非交易式儲存或production durability保證。驗證報告也採獨立新檔。

本輪實際命令及結果見 [接入驗收報告](validation_attempt_view_20261017/驗收報告.md)。原`validation_attempts_20261017`與`validation_20261017`保留為歷史；不能把舊瀏覽器或舊Android狀態當成本輪新頁驗收。

## 保留未完成

真實資料／盤中接入、自動明選規則、正式三種整理／生命階段／重要性、強勢延續分類、已持倉處置、機會成本／動能換股／資金閉環、校準勝率與績效未完成；三大最終目標未完成。1101／2884原案例核心覆核保留。Android本機開檔／真機效能與操作未驗收，雲端HTTP手機模擬不可代替。SQLite原事故根因未知；分類NOT_VALIDATED、完整交易資格NOT_EVALUATED。
