請接續股票系統M1，實作有來源的多參照「反應事實附層」，不重做圖表工程、不自訂主壓力或買賣規則。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
已核前節點：c0d063082bce74cd964ef4962d979c59204c4a84
固定真實圖成品：fff47915523fab8c8de8279de8bbb7a26b05647b
本輪交接：docs/visual-discussion/20261020_reaction_facts_contract/，研究成果提交見GITHUB_READBACK.json。先取分支最新，確認包含前節點與固定成品並讀後續交接，保留所有成果，不用main或舊ZIP覆蓋。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節，再全文讀本輪README.md、REACTION_FACTS_CONTRACT.md與本檔，讀facts.json、browser-observation.json及GitHub收據。沿讀前輪20261020_pressure_update_evidence/user-decision.json、README與WORK_HANDOFF，原graph_core／graph_diagnostics／cross_scale_chart契約及相關原碼。原39筆／月份主帶／6/3／1/27／5/13等案例已答，不重問、不重讀101圖、不重開0.4.3或舊Android按鈕。

在實際完整checkout依AGENTS執行python3 codex/bootstrap_m1.py --hydrate-missing；本輪Work只讀成品、未bootstrap，不冒用先前環境成功。準備失敗先診斷，不能刪檔／改指紋／覆寫合法差異強過；保持原歷史ZIP及後續成果。

目標是有限、獨立版本化純數值附層，UI只讀結果。先檢視現有等價功能，能重用就重用，補缺而非重建原核心。接受有來源／basis／frame／as_of／可知時間的明示參照；研究候選界依原確認日可用，原完成K欄位明示查詢可用但不稱自動主壓力。另分開原值可知與參照實際選取時間；後來查詢的30.50／27.40不證當時已選關，historical_signal_eligible不可填true。不要新增參照挑選算法，不把人工audit餵進graph_core。所有日期／價位案例只作fixture，不寫進生產常數。

按完整契約對每個參照各存原close/high/low的上／下／相等與精確差值、實體漲跌與較前收漲跌分開、相鄰保存K高低／區間幾何、原量分母窗口與MACD、完整跨越跌回路徑。等值不補成過破；缺價／量／零分母／MACD null／已知缺日或basis中斷保留原因，不跨缺口湊事件，不補假K。日內順序保持未知，不從high/low推回測完成。整體解除與primary_pressure_id、有效突破、量權重、行動仍未知，不由局部布林值清除全部壓力。

真實驗收例：5/14開30.30收30.35是紅K但低於前收31.10，當日高30.50低於前低30.90，量比前筆約3.28只作描述；5/19在30.05下、20／21再上、22再下，20／21最高仍低於30.50；10/16高27.70／低26.95比前筆雙端上移，收27.30在26.95上但仍低於10/14高27.40，低恰等26.95不證日內回測。保留5/19柱正而收在參照下、10/13柱略增仍跌回等反證。精確原值見facts，不能把閱讀窗或來源原高價寫成正式箱界。

執行契約列的同源前綴／追加未來不回寫／未可知參照／多參照同時不同位置／相等與近零精度／缺漏零分母／來源基底拒絕／原系統保留等有意義檢查。若接畫面，只做新附層最小唯讀呈現與必要實際HTTP／完整精度JSON核對，原頁與所有舊data/core/ID保持，不重建已完成真實K量MACD工程。不以舊7／47或35／60等數字充作本輪測試；本輪交接尚未實作模組或跑上述驗收，2張PNG只屬Work有限觀察。

使用者09:31已確認局部重返／突破與整體解除分別判斷，不再追問；本輪「繼續」不是新權重／策略批准。正式主帶辨識、區界、量口徑增量、衰減重要性、合併、直接承接、生命階段仍未知；primary_pressure_id=null。原左高群6.05／容許3.5700／餘量−2.4800及右低群3.25／容許2.4675／餘量−0.7825不變，不調35%或3／6／12%湊答案。來源末轉折／確認／研究離箱／人工終點分開；89版本／84幾何組非獨立型態，廣義後來非直接承接，不等長窗不排名。

Raw公司行動／五年Adjusted／歷史公布可得／9待核日期與日曆非窮盡／資料缺口／Darvas正文／SQLite未知保持。核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED；新Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。工程完成不等主壓力辨識或交易價值通過。

保留原核心參數策略庫歷史舊頁案例來源證據與main，不部署、付費、交易、發訊息或啟動子代理。一般可逆工程直接做；只有真正需新策略／重大架構的決策回Work。完成後源碼、成品、實測、失敗限制與續接入口保存同分支，逐檔GitHub回讀；未讀未測未執行不標完成。結束提供最新已核SHA、實際完成／未完成、下載入口及完整可貼Work續接指令。
