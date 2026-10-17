# M1 v0.19：結構與動態證據工程候選

本目錄是依 2026-10-17 最新產品回饋新增的獨立候選，**不是生命週期分類或核心用途驗收完成**。保留 v0.18 舊頁、原分析引擎、共同 schema、SQLite 及歷史結果；不遷移資料庫，不產生交易資格。

## 已定義及本輪選用的候選

`context.py` 的 `product-context-candidate/0.1` 只連接當日已保存的 structure-0.3-research／daily-sma-0.1：

- 相同主要／次級層級的已確認 pivot 形成波段連結。發生、首次觀察、確認日期分開。相同日期或相同種類的相鄰點保留歧義，不推論盤中順序；pending 只另存，不能連成確認波段。
- 最近兩個已確認主要高點與低點各自比較高低。最近確認主要低點所屬原支撐區是**明示的參照**，不是經驗證的重要性排名。`structure_id` 指候選來源／模式／Raw 公司行動段落，不宣稱已辨識一個市場生命階段。
- 區域保留原範圍、角色、失效規則、狀態及接觸事件；另列當前收盤位於上方／區內／下方。原 BREACHED → INVALIDATED；停用 → STOPPED；原有效區且收盤越過相反邊界 → CHALLENGED；其餘有效區 → NOT_BREACHED。不自行改變原區域的連續收盤失效門檻或支壓互換。
- 原主要低點已失效／受挑戰優先單獨揭露；否則主要高低點都抬高且參照未失守、都降低、混合及未知各自呈現。這是候選證據上下文，不是已批准趨勢／買賣分類。
- 主畫面區域群為「主要層級，且原有效／主要低點參照／當日狀態有變化」。不是距離現價、最近日期或合成分數排名。完整次級／歷史證據可展開。
- 支持、反證、缺證分欄。正柱縮短不等於結構破壞；下降均線與跨週期衝突不能被正面證據抵銷。跌回原已突破壓力區只列事實，不直接命名假突破。
- 每日 frame 連到前一 frame 與原 snapshot；有明確狀態、接觸變化才列候選原因，沒有變化不等於行情不變。

量價候選現象：最近完整 5／20 筆的股數均量、`(high-low)/close` 平均；當日量／前 20 筆均量。未知量保持 null，前期均量 0 時比例 null，不補值、不把原 SHARES_REPORTED 再乘一千。以 Decimal50、HALF_EVEN 計算；不宣稱持股集中、主力吸籌或惜售。

`macd.py` 的 `macd-12-26-9-sma-seed/0.1` 是未獲策略批准的工程候選：快 12／慢 26／信號 9；EMA 首值為完整窗口 SMA，後續 `alpha=2/(N+1)`；第 26 筆才有 DIF，第 34 筆才有 DEA／柱；柱=`2*(DIF-DEA)`。Decimal50、HALF_EVEN，輸出完整精度字串。缺價重暖機。Raw 在每個已知公司行動生效日或之後第一筆資料重暖機；Adjusted 僅用當時已生效事件、同一選定價格錨定計算及比較相鄰柱值。**不拿前一 frame 的另一個 Adjusted 錨定直接比較**。沒有金叉買入規則。

## 原料與當時資訊邊界

目前只有 6 組（8069／6488 Raw 與 Adjusted、1101／2884 Raw）、共 1490 個已保存日終時點；每組 179 或 283 筆，非完整股票生命週期。輸入版本必須明選，沒有自選最新。

`build.py` 是明確執行的離線候選生產器，透過 public read-only store 讀取舊快照。原 MA 直接使用保存結果；新候選 OHLC 明示使用既有 `structure.project_prices` helper、Decimal28 HALF_EVEN 投影，**不是舊 Adjusted 日線已保存的 OHLC**。介面只讀新輸出，不計算分析／均線／MACD、不補算舊結果或恢復資料庫。

同事件集合的投影基底可共用；每個 frame 的畫面與下載僅取到自己的 index。新事件建立不同基底；相鄰動能用本 frame 同一錨定的前一筆值。原資料及已生效事件 prefix hash 必須精確相符；MA 在同事件基底的完整 prefix 也須相符。週月只連接同源同日已保存並通過對齊的背景，其他日期明示 NOT_SAVED，不能取鄰日、期末或自算。

歷史公告時刻、完整公司行動及官方日曆尚未認證；「當時可知」僅指目前來源之有效日期／前綴契約，不能升格成已驗證的 point-in-time 市場資料庫。

生命週期 `stage=UNKNOWN`、修正狀態另為 UNKNOWN；正式型態未定義、盤中無資料、籌碼持有人／分點無資料。分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。

## 重現及使用

先在 repository root 執行 `python3 codex/bootstrap_m1.py --hydrate-missing`，保留已有修改，再進入 `股票系統M1_v0_18`。不用下載套件或 API key。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 product_candidate/build.py \
  --config cross_view/sources.json --structure-version structure-0.3-research \
  --output-dir product_candidate/output/replay-v019
PYTHONDONTWRITEBYTECODE=1 python3 product_candidate/verify_saved.py \
  --config cross_view/sources.json --candidate-dir product_candidate/output/replay-v019
M1_CANDIDATE_DIR="$PWD/product_candidate/output/replay-v019" \
M1_BROWSER_OUTPUT_DIR="$PWD/product_candidate/output/browser-v019" \
CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium \
node product_candidate/test_browser.cjs
mkdir -p product_candidate/tmp
TMPDIR="$PWD/product_candidate/tmp" PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -v
```

完全相同的候選再次匯出回報 EXISTING；不同內容／symlink 拒絕覆寫，應選新輸出目錄。這是獨立檔案防覆寫，不宣稱多檔交易式提交或 production durability。

`M1_v0_19_candidate.html` 為內嵌資料單頁，無網路請求。明選資料與日終日期後：讀取概覽及反證，日期滑桿重播，任意起訖、平移／縮放、價格尺度、同日期量與 MACD、JSON 下載。單指預設捲動；切到圖表平移才啟用單指 pan／雙指 pinch。沒有原生全螢幕時會明示頁內專注模式。下載保留當時完整數值與來源。

雲端瀏覽器實測僅透過 loopback HTTP，不能當成 Android 本機開檔驗收。實測報告、截圖與命令見 `validation_20261017/驗收報告.md`；工程資料追溯與合成案例不代表正式分類品質或使用者產品認可。

## 新增獨立嘗試／量先價核心（2026-10-17）

`attempt_evidence.py`（`attempt-evidence-candidate/0.1`）已可明確呼叫，處理人工明選的近期高點與左側區域上緣兩個嘗試關卡，以及左區最高量／量先價、盤中與收盤及後續跌回的時序證據。沒有把它自動接入原 build／viewer，不改舊策略或歷史。價格子條件與完整交易資格分開，沒有校準勝率或正式強勢股分類。

契約與限制見 [ATTEMPT_EVIDENCE.md](ATTEMPT_EVIDENCE.md)，本輪24項新測試、16項既有回歸及CLI讀回見 [新核心驗收報告](validation_attempts_20261017/驗收報告.md)。候選畫面接入、真實盤中及Android未完成；下一段依根目錄 M1_V019_ATTEMPT_CORE_HANDOFF.md 進行。
