請接續股票系統M1，實讀本輪新診斷後判讀原自動結果與人工整體結構的差異，不調參湊答案。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
必須包含交接631f6db9b17f666a283bc61b586bd4b77b27dd8f與原成品2d480bffcaebfa09768e04a283227effc3fc0a00。本輪source／成品固定提交57e3d9e55c226c5dd0e69fcbd26883d0da81667e；後續收據文件以分支最新為準。GitHub本輪已實下載87檔／70,735,165 bytes逐字相同、遠端ZIP CRC／8成員SHA及四份gzip解壓與ZIP一致，收據請實讀。若有後續先讀最新交接保留，不從main或舊ZIP覆蓋。不能讀取／下載／執行或保存時列實際錯誤，不假稱成功。

依序實讀：AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節、PROJECT_VISION.md及M1_V019_VISUAL_RULE_NOTES.md最新要求；再讀股票系統M1_v0_18/graph_diagnostics/README.md、validation_20261019/驗收報告.md、generated/review-diagnostics.json，以及本交付README／PACKAGE_VERIFICATION.json／SOURCE_HASHES.json／GITHUB_DOWNLOAD_VERIFICATION.json。本檔全文與docs/visual-discussion/20261019_graph_core_review/README.md、structural-comparison.json、browser-observation.json、WORK_HANDOFF.md均需實讀。必要時讀原graph_core契約及程式，不重下載／重讀101私人圖。

本輪Codex已在完整checkout重新bootstrap --hydrate-missing成功：0補檔、7差異保留，未沿Work舊失敗為成功。若需在新工程環境執行，再按AGENTS重新準備；只讀Work不能執行則明示，不冒充bootstrap完成。

新成品M1_v019_graph_diagnostics_v01.html，標頭「M1 圖形辨識追溯診斷 0.1」。ZIP在deliveries/m1-v019-graph-diagnostics-20261019/M1_v019_graph_diagnostics_v01.zip，24,735,759 bytes，SHA c8a534f517bdd0e5f648d6b94c0bde992b9b869d72ead727ce84a4a75c3c69ff；HTML16,401,279 bytes，SHA eb6d1e82da13db58a592d0868822fec9209bedfaf1ff4843440749677cad1baa。下載核SHA／CRC後解壓。完整latest診斷JSON在ZIP；Git以generated/diagnostics-代碼-latest.json.gz保存，解壓SHA收據在同目錄。小型review-diagnostics.json可直接讀。HTML原生gzip解壓，不需CDN；缺瀏覽器能力須報具體載入錯誤，不重試或繞過file://政策。

本輪實做純數值graph-recognition-diagnostics/0.1附層與獨立圖，原graph-recognition-research/0.1、原候選／參數／JSON／舊頁完全保留。原4854根OHLCV／MACD／SMA／source-frame／人工audit及預設呈現全欄位相等。仍每股15個共60已算分析日；所有真實K可查，不代表逐日均已算。分析固定1101／Raw／2026-10-16收27.30，非即時行情。

實測35 Python PASS（原核心21＋診斷14）、60原核心及60診斷重新執行＋60 oracle PASS；後續僅修正「研究界外」文字，數值封包逐位元相等、目前顯示原碼可重現。最終HTML45真實Chromium HTTP PASS／12完整精度下載，四寬16PNG、0JS錯誤／外部請求；不是舊115／72或398全套，也不是Android。初次大記憶體preview主動中止與首版45項／畫面、文字修正保留，不算最終數值／HTML測試混用。來源保留與GitHub回讀各有收據，實讀後才聲稱已核。

優先看以下新差異，不回到逐個小箱問卷：
1. 開追溯診斷選B77。「同末轉折的所有起點」找2023-05-02～2025-03-12被拒串：高群跨度6.05、容許3.5700、餘量−2.4800；極值證人含原40.25。6%確認轉折序列在六月起緣附近無六月起點，任意日／月份端點未被枚舉，不能說人工六月日期本身被_range拒絕。「看此串與原候選」用真實可放大圖比較，不把黃色診斷外包認成正式箱。
2. 切「同起點的後來末轉折」，看4/8延伸：低群跨度3.25、容許2.4675、餘量−0.7825。這是舊設定的具體原因，不證明人工月份主帶不存在，不改35%或3／6／12%湊相符。月份主帶精確端點／代表仍null，不追問月初月底當前置。
3. B44與B80同四來源幾何，5/13是末轉折，確認5/14／5/27；首次研究界外／研究破底6/2，前筆5/29。人工4/7～6/2含兩端39筆、5/13局部代表31.40、6/3在外已答，不能重問、刪原K或把25筆等於39筆。原未顯示是UI多樣性未勝出，不等引擎完全漏檢。各eligible／winner及原支配者可展開查。
4. B67→68→70→72→74→76→77為精確同尺度來源ID前綴發展版本；B44／80跨尺度同幾何另列較晚共同可知日；B89為不同起點局部子串。89版本與84精確幾何組都不是獨立型態數或accuracy，不硬合併、不刪歷史、不獨立計票。
5. B77原32個successor全保留，附層明示廣義後來候選與各來源起日／確認／關係可知時間，direct_successor_id=null；後來出現不等直接承接。幾何parent不等人工整體重要性階層。
6. 後續觀察窗B77=383筆、B44=349、B80=340、B88=31；到最低分別163／129／120／11筆，非同一長度。前等長量窗與事件／當日前1／5／20筆排除當日窗分列。不得把這些不等長描述升為公平重要性、衰減、量增或實際持股沉澱公式。

新圖操作只為讀上述結構原因：聚焦被拒串後可＋−／移圖／真實交易日查詢／24月返回，游標與K量MACD同步，定位不改分析日。下載graph-diagnostic-selection/0.1保留原core及新diagnostics的完整精度。若Work只看靜態圖不代填互動通過；若有限實開另記本輪實際scope，不沿Codex數字當Work重跑。

已答案例與理由全保留：1/27=2026-01-27／26.95，3/4、3/20轉折才確認，B88在9/1才確認；10/12上越、13跌回、14再越、15再跌回、16再越不可刪。6/3前箱破底／排除現箱、6/4原高27.45、39筆前箱／5/13、G2精確1/16～8/16、G1約九月～C／原代表、G3五日及原①④不重問、不混成新規則。0.4.3樣式已收束，不重開或索相同舊手機圖／JSON。

本輪只完成透明診斷，整體月份主帶、39筆正式歸屬／六月後整箱、正式分區／合併／界線／量口徑／增量／強度衰減／重要性／直接承接／生命階段仍未完成，primary_pressure_id=null。需要真正核心裁決才用具體可放大真實差異圖提出問題，不自行補門檻或以工程測試當辨識用途認可。新分析未經使用者批准。Raw完整公司行動／五年Adjusted／歷史公布可得、原資料缺口／Darvas正文未完整讀／SQLite未知根因保持；五年高不是全史高，日OHLCV不認證精確分價／剩餘持股。

Android NOT_TESTED_NEW_BUILD，雲端HTTP／觸控模擬不是實機；無需重開舊按鈕驗收。若自然取得新裝置證據，區分OBSERVED／USER_REPORTED／NOT_TESTED／BLOCKED，不重索同版已核舊檔。file://政策不重試、不繞過、不要求關閉保護。

一般可逆工作自行完成；原引擎、策略、庫、歷史、舊頁、案例、圖片庫與手機證據保留，不改main，不部署、付費、交易、發訊息或啟動子代理。把新的實讀、結構判讀、未決資格或可重現缺陷保存同一分支並逐檔核GitHub；不能執行或保存須明說。未測不得標完成，不用箱數／同價／畫出色帶代表核心功能完成。下一步已定規則或工程缺陷再交Codex，真正未定核心在Work；換模式必附包含最新已核提交的完整可貼指令。
