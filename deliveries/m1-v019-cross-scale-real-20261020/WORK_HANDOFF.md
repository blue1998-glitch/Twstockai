請接續股票系統M1，直接檢視新完成的真實跨尺度K／成交量／MACD比較圖，不再只加文字或用時間軸當K線。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
必須包含最新前交接cc71899668e1cd6f061af64739d279772a26287a與原固定診斷成品57e3d9e55c226c5dd0e69fcbd26883d0da81667e。本輪新source／成品固定提交fff47915523fab8c8de8279de8bbb7a26b05647b；GitHub本輪已實際回下載108檔／37,832,269 bytes逐字相同（含原固定診斷ZIP），新ZIP CRC／6成員SHA通過，收據見同目錄。後續連結與收據文件以分支最新為準；若分支更新先讀最新交接、保留後續成果，不用main或舊ZIP覆蓋。不能讀取／下載／執行／保存須列實際錯誤，不假稱完成。

依序實讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節，然後本目錄README／PACKAGE_VERIFICATION.json／SOURCE_HASHES.json／GITHUB_DOWNLOAD_VERIFICATION.json及本檔全文；股票系統M1_v0_18/cross_scale_chart/README.md、generated/source-acquisition.json、generated/artifact-verification.json、validation_20261020/驗收報告.md。沿讀PROJECT_VISION.md／M1_V019_VISUAL_RULE_NOTES.md最新要求、docs/core-recognition/20261020_work_diagnostic_read_review.md、20261020_cross_scale_structure_work_review.md、20261020_cross_scale_comparison_reader.html、20261020_cross_scale_reader_validation.md與原graph_core_review四份文件；舊人工案例與診斷資格保留，不重讀101圖片。

上一Work因NameResolutionError無法下載固定ZIP，只完成文字／時間證據軸，沒有取得真實K量MACD，紀錄不改寫。本輪Codex在完整checkout重新bootstrap --hydrate-missing實際exit0、0補檔／7差異保留；重新核原固定ZIP／8成員CRC及SHA／HTML SHA，實際解出1101全部1,213根2021-10-18～2026-10-16 OHLCV、原股數、MACD及SMA。source／Raw basis／frame／prefix／原core全部相同。這是新環境取得成功，不宣稱Work原網路已修復。

新成品M1_v019_cross_scale_real_v01.html，標頭「M1 真實跨尺度比較 0.1」。ZIP在deliveries/m1-v019-cross-scale-real-20261020/M1_v019_cross_scale_real_v01.zip，749,695 bytes，SHA256 894d93f852edce18f741695b96766210702c51be8b961916520fd3d29464d6c8。HTML2,232,879 bytes，SHA f5b3b4e5e03da1c8291ff5854e0a6dfbb974286fe5cfbcb9a466ec6e138203ee。下載HTML或解壓ZIP後開啟，無CDN／瀏覽器gzip需求。若Work不能下載二進位，可讀同分支cross_scale_chart/generated/comparison-data.json；它包含完整原OHLCV／MACD／SMA與來源、core、人工audit及比較附層，不再只有review摘要。無法實開時明示，不能以讀JSON替代互動驗收。

固定1101／Raw／2026-10-16收27.30，非即時。新增頁只讀結果，沒跑或改原核心／參數／策略／庫／歷史／舊頁，沒有新市場資料或五年Adjusted。MACD原列沒有日期，按原K線索引保存順序相配，未補造日期。範圍內已存OHLCV無空值不等日曆完整；原9個待核日期／公司行動／歷史公布可得限制保留，不補假K。

本輪實測7項定向Python PASS；真正重讀最終HTML及獨立JSON，與固定診斷成品逐值比較全部真實數列、來源識別與完整原core，全等；沒有冒稱重算60前綴。最終47真實Chromium HTTP／12完整JSON下載PASS，1280×900 DPR1、390×844／844×390／320×740 DPR2、原生滑鼠／CDP單指查詢和平移／雙指縮放、K量MACD與日期軸x座標／物理左緣寬度同步、來源／時點定位不改分析、跨休市逐記錄查詢、近期模式目前覆核層全關前後MACD像素相同（不擴稱所有模式逐張像素相等）、0JS錯誤／外部請求。28最終PNG，首個MACD欄位KeyError／0測試執行、18px日期軸錯位失敗與較早版證據保留。舊35／60／45／398都不是本輪重跑；不沿數字假稱Work或Android測過。

本輪Work優先看實際圖，不重做舊按鈕問卷：
1. 「跨尺度全景」直接看真實K量MACD上的七組來源：「人工月份閱讀」「B77原候選」「左擴被拒」「右延被拒」「人工39筆」「B44/B80同幾何」「B88近期」。圖上短圖例與勾選可區分，來源色塊／虛線外框用完整原K影線外包，不是正式價界；量底色與MACD分開。
2. 「主帶／拒絕串」可縮近長期脈絡。選左拒→定位來源及時點，查高群6.05／容許3.5700／餘量−2.4800與5/2／40.25等原證人；選右拒查低群3.25／容許2.4675／餘量−0.7825。這只是原轉折串拒絕，六月人工月份端點未被直接枚舉，不能否定整體主帶，也不能調35%或3／6／12%湊答案。
3. 人工主帶只有2023-06～2025-04月份精度，圖上463根、六月首筆／四月末筆是整月閱讀外包，兩端漸淡，精確端點／正式價界／代表仍null。不要把這些顯示日期寫成演算法答案或重新問月初月底。
4. 「39筆／同幾何」比較已確認人工2025-04-07～06-02／39筆與B44/B80來源4/8～5/13／25筆。5/13來源末轉折、5/14與5/27各自確認、5/29研究界外前筆、6/2研究首次界外與人工終點分別保存；下方日期軸○／◆／▼／■及日期按鈕可直接查詢。25不等39，跨尺度同幾何不是兩張成功票。5/13局部代表31.40、6/3前箱破底／排除現箱已答，不再追問。
5. 「近期／反證」看B88與真實1/27／26.95來源；3/4、3/20轉折才確認、9/1箱才確認，10/12越過、13跌回、14再越、15再跌回、16再越保留，不升確定突破或持股沉澱。1/27與原④1/29分開，原①④／G1G2G3及6/4高27.45不改。
6. ＋−、滾輪、預設拖曳查詢、切「移圖／雙指縮放」、約五年／24月／返回近期、逐真實交易日查詢都只改閱讀窗／游標，不移固定分析日。久遠K查詢是後來人工對照，不是當時訊號或每日分析回放。JSON新schema cross-scale-comparison-selection/0.1將完整data與display分開，價格／MACD保留原精度。

若需研究新核心，以圖中真正可見差異與已答整體觀點整理具體問題，不能將這次圖表工程當正式主壓力辨識完成。89候選版本／84幾何組不是獨立型態數或accuracy；同尺度前綴版本、跨尺度同幾何、不同局部串分開。原32廣義後來候選不等直接承接，direct_successor_id=null；383／349／340／31筆後續窗口不同，不用跌幅直接作公平重要性比較。

主帶／39筆正式歸屬／六月後整箱的自動辨識仍有差異；正式區界、量口徑／增量、強度衰減／重要性、合併／直接承接、生命階段未知，primary_pressure_id=null。新分析未獲使用者裁決，不硬編日期或新增門檻，不重問已答案例、不重讀101圖、不重開0.4.3或舊Android按鈕。

新頁Android NOT_TESTED_NEW_BUILD、使用者開檔分享流程及裝置效能未測；雲端手機寬度／CDP不是實機。若自然取得新手機圖／操作回報，分OBSERVED／USER_REPORTED／NOT_TESTED／BLOCKED記，不索相同舊檔。file://不重試不繞過、不要求停用保護。Raw公司行動、五年Adjusted、歷史公布可得、原缺口／Darvas正文／SQLite未知保持；五年高不是全史高，日OHLCV不測精確分價／剩餘持股。核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。

一般可逆工作直接做，需要執行新工程按AGENTS在新環境重新bootstrap；不能執行就列未測。保留原核心／參數／策略／庫／歷史／舊頁／案例／證據及main，不部署、付費、交易、發訊息或啟動子代理。成果與實讀／實測範圍、失敗及限制保存同一分支，逐檔核GitHub；未測不得標完成。已定規則／可重現工程缺陷交Codex，真正核心歧義在Work用真實圖討論；換模式時附最新已核提交與完整續接指令。
