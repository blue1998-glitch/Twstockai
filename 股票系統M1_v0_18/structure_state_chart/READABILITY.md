# P0-3 顯示修正版 0.2（數值核心仍 0.1）

本輪只改善三項已觀察的閱讀問題：預設事件列、手機有效繪圖寬度，以及來源日期／量觀察的語義。不是公司來源0.11，也沒有重定P0-3、角色、箱界、量或MACD規則。

`build_readable.py`只讀固定0.1交付HTML、五份JSON及build-verification，核SHA後做三個顯示幾何替換，並接上`readability.js`。沒有import或執行structure_state、reaction_facts、graph_core、指標producer或資料庫；不另做模式路由。原`build.py`、`patch.js`及全部0.1成品保留。新產物`M1_P03_structure_state_readable_v02.html`，封裝選擇的view_version為`p03-existing-chart/0.2`；snapshot/schema/所有核心數值及ID不變，五份JSON直接複製原bytes。

## 顯示差異

- 狀態列三個參照分開：原突破參照（研究上緣）、返回階段高點、研究下緣。價格、來源與事件由保存欄位產生，沒有股票／日期／價位答案硬碼。參照按鈕移出K線區仍可開原證據抽屜；圖內三色水平線／真實原K圓點按實際價位畫，軸外只提示，接近的兩條高點不共用來源。
- K線下方預設事件列顯示日期、收盤、相對三參照、狀態變化及原因。原突破與返回後狀態分開，原突破已發生的日期可同時是返回後P0-3證據不足。事件、關係及不足理由重用原records/events，不作JS數值判斷。每次選日期只顯示該前綴，不露未來高點或事件。
- 關閉舊疊圖時，右側保留64px價格／量刻度區；縮放鈕放在K與量之間的獨立空間，各44×44。390寬有效K線寬由225增至309px；價格範圍與資料不變。舊疊圖開啟時恢復其原140／110px保留區，避免舊關卡標籤錯位。K／量／MACD仍共x與游標，廣角與局部都保留，移圖／定位／縮放不改分析日。
- 預設「量觀察」中性呈現較前一保存筆增加／減少／相等及兩筆原量／日期，不稱好壞，不是整帶代表量、最大量比較或突破資格；僅讀原核心證據代碼。原supporting/opposing/missing與全部原量、MACD仍可在JSON／抽屜溯源，不刪不改，不用量或MACD取消價格過線。
- 抽屜及下方可展開來源日期欄，分開原價位K日、候選來源末轉折日、候選確認日、原值可知日、角色可知日、實際後來選取時間。RESEARCH_BOUND的occurred_at仍是原候選末轉折，不改schema或日期值；原價位K日取原evidence.source_k_dates，直接K取occurred_at。直接K的候選日期顯示不適用，不互借。

所有參照仍是後來明示研究角色。B88正式price_bounds=null，並沒有因顯示更清楚而升格人工正式原箱；此單次返回階段不是完整回檔已核定、自動選帶或市場樣本準確率。

## 工程重現

完整checkout依根及子AGENTS準備後，在股票系統M1_v0_18：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m structure_state_chart.build_readable --output-dir structure_state_chart/output/NEW_EMPTY_LEAF
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_structure_state_readability.py -v
P03_READABLE_DIR=structure_state_chart/output/NEW_EMPTY_LEAF P03_READABLE_EVIDENCE=structure_state_chart/validation_readability_20261024/NEW_RUN node structure_state_chart/test_readability.cjs
```

建置只沿庫內固定0.1原件，無網路；來源核對或顯示hook不合即拒絕，不覆寫不同輸出。測試用臨時127.0.0.1 HTTP真實Chromium，不是網站部署、不重試file://。正常使用者直接看GitHub新PNG，不需手機搬檔、終端或架伺服器。

本輪結果／失敗／未測見`validation_readability_20261024/驗收報告.md`；歷史65 Python／94 Chromium不當本輪重跑。無依賴變更、無新來源GET、producer、每日淨帳、六方案或Android實機。來源0.10／全部parent、Raw／UNKNOWN／歷史及main不變。

execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。完整公司行動、個人權利／淨分配、Raw／五年Adjusted／歷史公布／主檔／SQLite等未知及全部舊警告保留。沒有自動完整帶、全市場辨識、策略／換股或資金飛輪完成宣稱。不部署、付費、交易、訊息或子代理。
