請接續股票系統M1，驗看新自動圖形辨識研究核心的實際結構與反證，不再重做圖片首輪或舊樣式。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
本輪成品提交：2d480bffcaebfa09768e04a283227effc3fc0a00
必須包含前交接83506ff70c707db46c90d642396ed1c0cc6e268a。
先核分支與祖先；若有更新讀最新交接並保留，不用main／舊ZIP覆蓋。後續收據／交接提交以最新分支為準。不能讀GitHub／下載／執行或保存須列實際可見內容與錯誤，不假稱完成。

依序讀：
1. AGENTS.md
2. CONTINUE_IN_WORK_MODE.md最上方
3. M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節與原完整指令
4. PROJECT_VISION.md、M1_V019_VISUAL_RULE_NOTES.md及M1_V019_IMAGE_LEARNING_HANDOFF.md最新要求（不重讀101圖片）
5. 股票系統M1_v0_18/graph_core/README.md、graph_core_chart/README.md及其validation_20261019/驗收報告.md
6. graph_core_chart/generated/recognition-audit.json（小型描述／敏感度／人工差異，位於同專案內）
7. deliveries/m1-v019-graph-core-20261019/README.md、PACKAGE_VERIFICATION.json、SOURCE_HASHES.json、GITHUB_DOWNLOAD_VERIFICATION.json及本檔全文
8. M1_V019_PRESSURE_CHART_ANDROID_ACCEPTANCE.md最新紀錄與交接指定的公開人工案例。私人原圖／逐圖資料保持Drive，不進公開Git。

Codex本輪完整checkout與3歷史ZIP SHA已重新核實，原bootstrap --hydrate-missing實跑成功：0補檔、7差異保留；沒有拿Work失敗當成功。Work先前PREPARATION_FAILED環境紀錄保留為歷史。若需要在新完整checkout執行再按AGENTS重跑，不能執行明示，不改指紋／刪檔強過。

新頁：M1_v019_graph_recognition_v01.html，graph-recognition-view/0.1。
ZIP：deliveries/m1-v019-graph-core-20261019/M1_v019_graph_recognition_v01.zip。
ZIP 5,040,045 bytes，SHA256 934c54ec033de14d402cb4b8110ed53e9a99b311a934144f9139950c05046783。
HTML 13,748,260 bytes，SHA256 fbca1e1d7e82d5dc9dcca8da0d3c8619f59431c1119d2cd8cb4c8ffc8293a724。
解壓開新頁，標頭「M1 圖形辨識研究主圖 0.1」，1101／Raw／2026-10-16收27.30，非即時今日。K線／成交量／MACD可同步放大平移查詢。已算分析日每股15個、共60前綴；回放不是所有歷史日，價格與查詢保留全部4854真實記錄，不補休市K。其他分析日需CLI另建，不在UI補算。

已實作純數值graph-recognition-research/0.1，自動從當時收盤前綴找多尺度反覆高低箱、父子包含、相關壓力、假突破跌回、破底後新箱、量與下跌反證；人工答案不輸入核心。研究設定3／6／12%反向及35%高低群穩定度未獲批准，沒有偷偷採教材或Darvas正式規則。正式區界仍null，主壓力多目標衝突保留primary_pressure_id=null；量總和／均量／最高柱／前1、5、20筆比較只是明示研究描述，不是整區量口徑、沉澱或增量資格。

本輪21項新Python通過，含截短前綴／未來改動不回寫、同價／日序歧義、假突破／破底新箱、缺量真0／缺價日期／基底／可得／未完成K、純核心無UI／SQL／網路／舊引擎相依。全部60辨識前綴重新計算、原OHLCV／MACD／SMA／frame逐值相同。最終HTML115項真實Chromium HTTP通過，72次完整下載對Python oracle；ZIP CRC／9成員SHA實核。原失敗（均量窗口假設、快取NameError、快速下載逾時、刻度碰撞）與修正、最終圖保存。不是辨識準確率／核心用途或Android通過，file://阻擋未重試／未繞過。

這次優先做核心差異判讀，不再回到小箱代表逐一問卷：
A. 看新自動主圖及研究箱列表：長脈絡與局部箱是否呈現有意義的關係，哪裡漏掉／切碎／合併不當，應從最新27.30回看更左的重要壓力。預設顯示多種證據只為閱讀，不是已批准的唯一重要性排名。用可放大真實新圖指出具體缺口，保留來源／箱ID／分析日／首次可知日及反證，不再只數框與標記。
B. 必須先承認已知差異：1101本設定89箱／171轉折／25研究前緣；1/27／26.95有兩尺度同價來源，但3/4、3/20才確認，不能倒灌1/27已知。人工4/7～6/2／39筆沒有完全同起訖的自動匹配；使用者2023-06～2025-04月份大帶未完整重現。不要為通過測試把人工日期寫入演算法或調參湊答案，不把同價匹配當準確率。敏感度報告顯示設定會改變候選，並非最佳參數或已訓練模型。
C. 已答1/27較重要理由、6/3前箱破底／排除現箱、6/4原高27.45、5/13局部代表31.40、前箱39筆與G2精確日期不重問；保留原①④及G1G2G3。主帶只有月份精度，正式端點／代表／價格區界／量口徑／重要性公式仍未知，不追問月初月底當前置。以新自動錯誤與已答整體結構作對照，有真正核心歧義才問具體圖，不重開已答判讀。
D. 可看10/12～16已算前綴回放，查收盤越過／跌回歷程與量口徑，不能稱確定突破。下載graph-recognition-selection/0.1保留原字串、source/frame/basis/prefix、core與後來人工對照；UI約數不降低JSON精度。若只讀靜態圖不代填操作通過。

工程、辨識品質、Android、核心用途與交易價值分開。新頁Android起始NOT_TESTED_NEW_BUILD；如自然取得新裝置畫面／操作回報，分OBSERVED／USER_REPORTED／NOT_TESTED／BLOCKED記，不要求同舊圖／JSON或完整重做按鈕QA。原0.4.3樣式USER_REPORTED已收束，不開0.4.4樣式階段。原file://政策拒絕不重試／繞過／停用保護。

101原圖／91首輪／13複讀與私人Drive成果保留，不重下載／重判，不假稱已訓練或知道所有逐圖細節。正式區界、量口徑／增量、重要性／衰減、自動門檻、生命階段仍未定；Raw完整公司行動／五年Adjusted／歷史公布可得／原資料缺口／Darvas正文／SQLite未知保持。五年高不是全史高，價格量能不能測精確剩餘持股。核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。

一般可逆工作直接做。需要新規則或可重現核心問題交Codex，附新圖／箱ID／source／frame／as_of、步驟、反證及已確認規則，不改原策略或人工案例。保留原引擎、庫、歷史、舊頁與證據；不改main，不部署、付費、交易、發訊息或啟動子代理。

把新的結構判讀、缺口及接續保存同一分支並確認GitHub；不能保存須明說。未測不標完成，不以「已畫箱／測試通過」替代有用辨識完成。結束列實際完成／未完成、入口、最新提交與下一步Work或Codex；換模式時附完整可貼指令。
