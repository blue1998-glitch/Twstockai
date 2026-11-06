請接續股票系統M1，直接驗收本次0.3人工價量時間區域主圖的新差異，不把UI接入當成核心用途通過。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
本輪成品提交：31d80971b265942eb3d7573fddf00f6782f20a55
必須包含原交接7569d12b249080d305f2cf0dbd36b35485785bfb。
先確認分支及祖先；若已有更新，讀最新交接並保留成果，不用main或舊ZIP覆蓋。此指令若在後續提交才保存，以其所在最新分支及收據為準。不能存取GitHub／附件或執行時，列實際可見檔案、能力與錯誤，不假稱已讀／已測。

依序讀：
1. AGENTS.md
2. CONTINUE_IN_WORK_MODE.md最上方
3. M1_V019_MANUAL_REGIONS_INTEGRATION_HANDOFF.md最新節
4. PROJECT_VISION.md與M1_V019_VISUAL_RULE_NOTES.md最新要求
5. 股票系統M1_v0_18/region_chart/README.md及validation_20261018/驗收報告.md
6. deliveries/m1-v019-manual-regions-v03-20261018/README.md、PACKAGE_VERIFICATION.json、SOURCE_HASHES.json及GITHUB_DOWNLOAD_VERIFICATION.json（若尚不存在，不能假設已遠端核對）
7. M1_V019_PRESSURE_CHART_ANDROID_ACCEPTANCE.md最上方
8. docs/visual-discussion/20261018_g1_region_review/user_review.json、g1_region_review_facts.json及20261018_g2_endpoints/user_review.json、endpoint_source_verification.json。
有完整checkout且需要執行才依AGENTS跑python3 codex/bootstrap_m1.py --hydrate-missing，保留差異，不拿嚴格舊基線覆寫；沒有執行工具就明示。

新版：M1_v0_19_manual_regions_v03.html，view_version=manual-region-chart-view/0.3。
小ZIP：deliveries/m1-v019-manual-regions-v03-20261018/M1_v019_manual_regions_v03.zip。
ZIP SHA256：ef258e1dfa1bd965168f630c642b56475cc132fc7184b85dbbfe999e1fde2f9b（4,371,652 bytes）。
HTML SHA256：0a1513b361c1473c4e38bb3c5db2f3477054fe2bb4779592f31b5b73fc84bb8e（36,744,203 bytes）。
HTML另在股票系統M1_v0_18/region_chart/generated/。從交付入口下載固定提交原始ZIP並核SHA，解壓後確認標頭「M1 價量區域主圖0.3」、1101／Raw｜新官方日線／2026-10-16、日收27.30／預設24月486根。不是舊0.1／0.2。不要重試或繞過已知file://管理政策阻擋；若手機開檔失敗，記機型／瀏覽器／開檔方式／錯誤，保留未測，不要求停用保護。

已完成工程：G1／G2時間區域與C開放參照、原代表點及來源日量、聚焦／返回、拖曳查詢與移圖分離、逐交易日完整OHLCV、K量MACD同步、獨立未提交草稿下載。新Python16及完整383、本版真實Chromium208 HTTP／44標籤／55區域已實際跑完；244源檔／4854新Raw+1490原frame／50oracle及ZIP CRC／逐檔SHA已核，見報告，不把這些當成Android或核心用途PASS。原file://阻礙本輪未重試。前兩次新區域測試失敗是欄位名稱／完整base與前綴的測試假設，報告已保存；最終HTML SHA重跑通過。

本輪請只收新版差異，以最少新證據確認，不重開整套舊按鈕驗收：
A. 先確認0.3身份與入口。手機直向按「G2價量帶」：時間帶2023-01-16～2023-08-16、代表5/2高40.25；「區域證據」能讀兩端原OHLCV。起點36.55／36.90／36.15／36.50／34494589股；終點36.55／36.60／36.00／36.05／30022247股。兩日期已確認，不再問使用者重選。
B. 關閉證據、按G1價量帶：九月不確定起緣→C 2024-01-19 low31.80，原11/28 high35.50保留；9/14同高、10/18及11/30量峰仍來源日期，不把G1日量當整帶量。C後只有終點未定的開放參照。返回24月仍486根、分析日10/16不變；G2／G3超軸仍提示、不強拉價格軸。
C. 預設「拖曳查詢」，單指橫拖只移同日游標／OHLCV，不移窗、不改分析日。再選「單指移圖／雙指縮放」確認可移窗／縮放，再回查詢；直／橫各觀察一次是否遮擋或橫向溢位。若使用者只回「成功」，記USER_REPORTED；看到原圖才標OBSERVED，不假稱直接觀察操作。
D. 主圖下查詢交易日選2023-01-16，再按兩次「▶查詢」應讀1/17→1/30，跨休市不造K；K／量／MACD同日，分析日仍10/16。新查詢讀值是原始OHLCV全精度。
E. 「選點草稿」記1/16起點與8/16終點，可複製或下載獨立JSON，status=DRAFT_NOT_SUBMITTED_NOT_APPROVED，完整code／source／frame／chart_base／analysis_as_of與OHLCV；不是批准案例或自動提交。重開、切來源／分析日清空，逆序不擅交換。新版主要「下載JSON」應manual-region-chart-selection/0.1，含manual_regions及4來源指紋，原manual_hurdles／原數值仍保留。只有真的要驗手機下載精度才收本版新原檔，不重索舊JSON。

新版0.3 Android起始NOT_TESTED_NEW_BUILD。0.2舊PARTIAL_EVIDENCE_OBSERVED及指定標籤差異已收束，所有舊原圖／原JSON保留，不重要求同版相同檔。請逐項記OBSERVED／USER_REPORTED／NOT_TESTED／BLOCKED，別由少量成功推定全Android或核心用途通過。先協助使用者按上述少量操作看真實新差異，再以具體真實圖討論主圖用途；不用人工色帶／圓點數量代替核心分析完成。

已確認G2精確起訖及代表點不要重問。G1仍大約2023年9月至C，精確起日null；價格區界、整區量／量口徑、增量、自動分區／選關、強度／衰減、生命階段仍未知，不自訂門檻。C右側是使用者定性新平緩判讀，不認證精確持股或所有後續K歸屬，不把4/30固定為終點。原①26.10／④26.85及G3五個50.20日期保留，不改為全市場自動訊號；2026-10-18後來人工覆核不能倒灌10/16或更早當時已知。

完整Raw公司行動／五年Adjusted／歷史公布可得未核，Raw高不認證共同校正壓力；五年高不是全史高。日OHLCV不代表精確分價／剩餘套牢持股。TWSE補證未接入原產品稽核、TPEx主證及原缺價零量等資料缺口、SQLite未知根因及file政策阻礙照最新交接保留。Darvas箱型正文未完整讀，不能自稱已採用其規則。

保留0.1／0.2、原引擎策略／庫／歷史／舊頁／JSON／手機證據，計算與顯示分離；不改main，不部署、付費、交易、發訊息或啟動子代理。一般可逆工作可直接處理，核心未決用具體圖問，不發明門檻。可重現工程缺口才交Codex，附本版source／frame、實際步驟、原圖或新JSON與錯誤；尚未測不得標完成。

把本輪新版差異紀錄、使用者回報與交接保存同一分支並確認GitHub；若工具不能寫／確認須明說。結束提供實際完成／未完成、成品入口、最新提交，以及下一步用Work或Codex。若需轉Codex，給完整可貼指令；以後每次回Work也附完整可貼Work指令。
