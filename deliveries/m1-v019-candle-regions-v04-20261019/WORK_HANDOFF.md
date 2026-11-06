請接續股票系統M1，只驗新版0.4「貼合真實K線影線的外框」差異，不重開整套舊功能驗收，也不把UI修正當核心用途通過。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
本輪成品提交：d83f92cb47fe581ee76ee05a6f944cd5abc56434
必須包含原交接570bfd4a4e99f5672a1666d28b6541a150b55dd6。
確認分支與祖先；若有更新，先讀最新交接並保留後續成果，不用main／舊ZIP覆蓋。若本指令後有交接收據提交，以最新分支為準。工具無法讀GitHub／附件、執行或保存時，列實際可見內容與錯誤，不假設已完成。

依序實讀：
1. AGENTS.md
2. CONTINUE_IN_WORK_MODE.md最上方
3. M1_V019_CANDLE_BOUNDED_REGION_HANDOFF.md最新節及原交接全文
4. PROJECT_VISION.md、M1_V019_VISUAL_RULE_NOTES.md最新要求
5. 股票系統M1_v0_18/candle_region_chart/README.md及validation_20261019/驗收報告.md，含extents/實際前後圖
6. deliveries/m1-v019-candle-regions-v04-20261019/README.md、PACKAGE_VERIFICATION.json、SOURCE_HASHES.json及GITHUB_DOWNLOAD_VERIFICATION.json（沒有收據不能自行宣稱遠端驗證）
7. M1_V019_PRESSURE_CHART_ANDROID_ACCEPTANCE.md最上方
8. region_chart/validation_android_20261019/evidence-0851.md、visual-review-0851.json與兩張原圖，以及交接指定G1／G2原案例／端點核對文件；上述region_chart在股票系統M1_v0_18下。
若有完整checkout且需要執行，按AGENTS跑python3 codex/bootstrap_m1.py --hydrate-missing，保留差異；不能執行就明示，不以嚴格舊基線覆寫。

新版：candle-region-chart-view/0.4，M1_v0_19_candle_regions_v04.html。
標頭實際為「M1 K線範圍區域主圖 0.4」（版號前有空格）。
ZIP：deliveries/m1-v019-candle-regions-v04-20261019/M1_v019_candle_regions_v04.zip。
ZIP 4,372,484 bytes；SHA256 0a759763dbebf562fa009097de3dc580a5ea296dc307b048366eaf0c0ca60cfc。
HTML 36,783,169 bytes；SHA256 8642986a70a1c315046327b4ec97452eae19ba78fbe619a713ce2965de42d44f。
HTML另存股票系統M1_v0_18/candle_region_chart/generated/。下載固定成品提交ZIP、核SHA並解壓；不是舊0.3。若手機開檔失敗，記機型／瀏覽器／開檔方式／具體錯誤，保留未測／受阻；原file://管理政策拒絕不重試／繞過，不要求停用保護。

本輪工程已完成：價框只包所選真實日K影線、量框在volume pane獨立包來源柱，MACD不再有價量區域底色。完整選段extent在縮放平移時固定，只裁切，不拉價軸、不把畫外真實界線假貼邊。離線Decimal保留來源精度與選段指紋，display extent獨立於formal pressure bounds；主下載schema manual-region-chart-selection/0.2加region_display，原manual_regions／manual_hurdles及舊值保留。原代表點／①④／G3五日、查詢移圖、OHLCV、分析日、前綴、草稿保留。

Codex本輪實際398 Python（含15定向）及真實Chromium208 HTTP／44標籤／55操作／32外框通過，最終HTML SHA一致；244源檔／4854新Raw+1490原frame／50oracle、凍結0.3及ZIP CRC／解壓SHA核對。首次新測試匯入失敗已保留，修正順序後通過。不是搬前版383／208／44／55作新通過；這些不代表Android或核心用途。整體HTTP runner仍保留舊file政策阻礙，這輪未重試。

請協助使用者只驗新的外框差異，最少必要新證據即可：
A. 自然確認0.4標頭、1101／Raw｜新官方日線／2026-10-16、日收27.30／預設24月486根；按「G2價量帶」。查看所選2023-01-16～2023-08-16的136根外包框，上界含5/2影線40.25，下界含1/17影線35.90；日期左右端貼實際K寬。量框與價框分開，MACD無區域底色，K／刻度／原線標籤／＋−不被遮。可收一張本版新圖，不重索已保存0.3兩圖。
B. 「G1價量帶」查看九月近似起緣虛線、左邊未閉合、到C參照，原11/28／35.50代表點不變；C後仍終點未定，無假封閉框。G1顯示31.35～35.50及97筆只是近似顯示錨外包，不將9/1批准為正式起日。只問本次新畫法是否符合需求，不追問已確認G2日期或重開未決策略。
C. 放大或平移至G2的部分K線：外框仍來自完整136筆，不用可見子窗重新取高低；真高40.25若畫外，不應貼頂造一條新價格界線。量框只在量pane裁切。返回24月仍486根、分析日10/16；可在方便的直／橫方向看一次新框是否可讀，不強迫重測全部手勢／草稿／跨休市流程。
D. 只有實際要驗手機新JSON下載精度時才收0.4新原檔，核manual-region-chart-selection/0.2、region_display／原人工層／source／frame／basis／分析日／原字串；不要重索舊JSON。否則下載與其他未測保持未測，不以一張圖代填。

0.4 Android起始NOT_TESTED_NEW_BUILD。舊0.3-family兩圖為PARTIAL_EVIDENCE_OBSERVED_VERSION_UNCONFIRMED，舊0.2部分證據及各項紀錄原樣保留，不搬作0.4通過。逐項記OBSERVED（實讀新原圖）、USER_REPORTED（使用者操作回報）、NOT_TESTED／BLOCKED。靜態圖不代表完整操作序列，少量成功不等於全部Android或核心用途PASS。

G2精確2023-01-16～2023-08-16、代表5/2／40.25不變，不再追問。35.90～40.25只為可逆顯示外包，不是正式壓力區界、分價或精確套牢持股。量框最高保存柱82,247,780股不是整區量／策略最大量。G1精確九月起日、正式價格區界、整區量／量口徑、增量、自動分區／選關、強度／衰減、生命階段仍未定，不自行補門檻。C後終點未知，不固定4/26或4/30、不分類全部後續K。

Raw完整公司行動／五年Adjusted／歷史公布可得未核，Raw高不認證共同校正壓力、五年高不是全史高；原資料缺口、TWSE補證未接入舊稽核／TPEx主證、零量缺價及SQLite未知根因保留。Darvas箱型正文未完整讀，沒有採入規則。新畫法不代表核心用途認可或全市場自動辨識完成。

保留0.1／0.2／0.3、原引擎策略／庫／歷史／舊頁／JSON／手機證據，計算與顯示分離；不改main，不部署、付費、交易、發訊息或啟動子代理。一般可逆工作直接處理。可重現工程缺口才交Codex，附版本／來源／frame、步驟、原圖及必要新JSON／錯誤；未決核心用具體圖釐清，不發明門檻。

把新增外框差異紀錄與交接保存同一指定分支並確認GitHub；不能寫／確認須明說。未測不得標完成。結束列實際完成／未完成、成品入口、最新提交與下一步Work或Codex；換模式時附完整可貼指令。
