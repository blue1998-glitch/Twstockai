# M1 人工價量時間區域主圖 0.3

獨立接入已覆核的1101／新官方Raw／2026-10-16人工案例；不改0.1／0.2頁面、原數值引擎、庫或歷史。只匹配code／source_id／frame_id／chart_base／分析日。此版本是UI接入，核心用途仍NOT_ESTABLISHED，Android為NOT_TESTED_NEW_BUILD。

- G1：約2023年9月→C(2024-01-19 low31.80)。九月斜線表示精確起緣未知，不將9/1作正式起日或計量窗；原11/28高35.50、9/14同高及10/18／11/30來源日量各自保留。
- G2：2023-01-16～2023-08-16精確時間帶，原5/2高40.25不變。兩端10欄位直接核對原檔；時間帶不是價格矩形、正式整區量或自動區域。
- C右側：只有開放虛線參照，終點未知，不把4/30或所有後續K線當成已核定平緩帶／持股穩定。
- 原①26.10／④26.85和G3五個50.20來源保留；代表點卡片預設折疊，軸內線標籤保留，超軸仍提示而不改價軸。

操作：預設拖曳查詢只移游標；明選「單指移圖／雙指縮放」才拖曳移窗。縮放、聚焦、18／24月、約5年及查詢日期不改分析日。K／量／MACD共用窗與游標；逐交易日前後鍵跨休市讀真實OHLCV原值。按「以游標日回看分析」才變更分析日，較早日期不套本例人工層。原完整離線檔含後續可明選資料，但目前可查、顯示、下載只用分析日前綴。

「選點草稿」記起／終點及下載獨立JSON，含來源、基底、frame、分析日及完整OHLCV；可長按複製。只存記憶體，重開／切來源或分析日即清空；反向點不自動交換。狀態DRAFT_NOT_SUBMITTED_NOT_APPROVED，不寫入已批准案例，不發送或自動保存至GitHub。主要分析下載另加manual_regions，原欄位值與精度保留。

## 重建與實測

先在根目錄依AGENTS執行`python3 codex/bootstrap_m1.py --hydrate-missing`；以下在`股票系統M1_v0_18/`執行，使用新的output葉目錄，immutable publisher拒絕覆蓋不同內容。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m region_chart.build --output-dir region_chart/output/my-regions-v03
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_manual_regions.py -v
PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/product_candidate/tmp" python3 -m unittest discover -s tests -v
python3 -m region_chart.verify_artifact --html region_chart/output/my-regions-v03/M1_v0_19_manual_regions_v03.html --history pressure_chart/data/history-20261018/history-candidate.json --oracle region_chart/output/my-regions-v03/selection-oracle.json --report region_chart/output/my-regions-v03/artifact-verification.json
M1_HURDLE_DIR="$PWD/region_chart/output/my-regions-v03" M1_HURDLE_BROWSER_OUTPUT_DIR="$PWD/region_chart/output/checks-general" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node region_chart/test_browser.cjs
M1_HURDLE_DIR="$PWD/region_chart/output/my-regions-v03" M1_LABEL_BROWSER_OUTPUT_DIR="$PWD/region_chart/output/checks-labels" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node region_chart/test_labels.cjs
M1_HURDLE_DIR="$PWD/region_chart/output/my-regions-v03" M1_REGION_BROWSER_OUTPUT_DIR="$PWD/region_chart/output/checks-regions" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node region_chart/test_regions.cjs
python3 -m region_chart.package --html region_chart/output/my-regions-v03/M1_v0_19_manual_regions_v03.html --output-dir region_chart/output/package-v03
```

實際結果、最終HTML SHA、曾失敗的測試假設及畫面見[本版驗收報告](validation_20261018/驗收報告.md)。已知file://管理政策拒絕只保留原紀錄，本輪不重試／繞過；HTTP真實Chromium與觸控模擬不當作Android開檔／實機通過。Playwright使用環境已提供安裝，不需新依賴或常駐服務。

## 資料與分工

`regions.py`離線驗來源指紋、精確案例／原檔欄位並供顯示索引；`build.py`在凍結0.2數值payload之上僅加獨立manual_regions；`viewer.js`／`regions_viewer.js`讀來源列與prepared圖層，不重算指標或策略。顯示padding僅閱讀範圍，非區域邊界／歸屬。原JSON不回寫，其原NOT_IMPLEMENTED是當時歷史，新wrapper另記接入狀態。

G1精確起日、價格區界、整區量及量口徑、自動分區／選關、增量、強度／衰減、生命階段仍未定；不得用視窗最高低／總量代填。Raw公司行動、五年Adjusted及歷史公布可得未驗證；Raw舊高不認證共同校正壓力，五年高不當完整歷史高。TWSE六日Work補證未接入舊產品稽核、TPEx主證及原零量缺價列等缺口保留；SQLite根因未知。Darvas正文未完整閱讀，無採入箱型規則。非即時、非交易指令，classification NOT_VALIDATED／action NOT_EVALUATED。

成品及完整可貼Work指令見[交付入口](../../deliveries/m1-v019-manual-regions-v03-20261018/README.md)。舊版及手機證據保留；只收新版差異，不重索舊檔或重問G2起訖。
