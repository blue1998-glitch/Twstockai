# M-OBS1｜量價事件雷達

直接試用：[純合成手機示範HTML](Twstockai_OBS1_SYNTHETIC_DEMO.html)。從GitHub檔案頁選「Download raw file」，在Android下載目錄用瀏覽器開啟。程式碼頁不是可操作網站；若瀏覽器拒開或顯示文字，不需改安全設定，回報畫面即可。OBS1本機HTML及Android實機未驗；UX1「操作ok」僅為使用者回饋，不能擴稱本雷達或完整私人資料已驗。

## 操作及事實範圍

既有工作台底部「雷達」→選首次可觀察日期、原事件類別及市場→展開全部原候選→開啟原圖。箱事件可聚焦原箱及原證據；高點參照事件開對應個股，保留原pivot_id與事件位置，可由詳細資料／原JSON查核，不冒充某個箱。搜尋、返回、圖形及原下載仍沿UX1。

只讀boxes及reference_candidates的path.events，不呼叫核心或建立新事件模型。原reference沒有id時沿pivot_id，事件沒有獨立ID時保留null，以result_id、候選ID、JSON pointer回查，沒有發明正式事件ID。保留原類型、發生日、first_observed_at、候選confirmed_at、來源／基底／前綴指紋與兩層qualification。量證據僅標示原事件是否附有描述，不另定放量、突破或交易規則。

按股票＋事件類別聚合；股票數用獨立identity去重，原候選事件筆數另列，展開不截斷候選ID。列表每頁50組可翻頁，不以筆數排名。預設只整理當批as_of首次可觀察事件，不把舊事件貼成新日訊號；合成示範明示額外日期覆蓋，不冒稱完整歷史索引。沒有事件顯示空狀態。

停止比較事件與普通位置事件分開；歷史事件跨後續重置標為HISTORICAL_ONLY_NOT_CURRENT_COMPARABLE，不代表今日可比。缺價／reset當天的非停止事件、錯股票／市場／截止、原結果指紋衝突或來源拒用均拒絕建立該股索引。UNKNOWN歷史公布時間仍是回顧性資料，不認證當時已可交易。pending只記候選數，不列為已觀察事件。

## 來源與測試證據

本輪5個唯一Python方法（4投影＋1新頁私人服務保護）、12組合成手機流程、2組真實手機尺寸開圖／下載通過；同方法重跑不加總。真實四股索引共27候選事件／3檔，2884為0，不是27檔。見tests-final.log、tests-chronology.log、tests-security.log、browser-verification.json、real-browser-verification.json及real-verification.json；各自是定向單元控制、合成手機操作與既存四股真實結果核對，不能相加為市場樣本或策略績效。首輪合成序列只出現INITIAL_CLOSE_LOCATION，追加最小虛構日線後由未改核心產生多種類事件；沒有手寫假核心結果。示範含虛構週末日期，只是合成機制，不冒真實市場交易日。

首次瀏覽器helper選了合成輸出不存在的CLOSE_BELOW_RESEARCH_RANGE，timeout留在browser-first.log及browser-failure.json。空狀態oracle不變，改選原輸出中實有、但B股沒有的CLOSE_CROSS_DOWN。原core／來源／事件結果未為測試而改。Python同方法中間批不累加。

正式版與示範版共用market_preview、UX1及radar.js。只新增輕量投影，主圖仍按需一股載入；不載全市場完整歷史到手機。新頁獨立market-obs1-v01，原UX1及舊成品不覆寫。Journal、登入／白名單、core0.2、MA／MACD數值及原viewer不變；無SW／離線快取、CDN或新資料庫。

## 保留邊界

當前FM3私人根仍不可讀，不能宣稱全1469圖／全市場實際雷達已驗。現存真實驗證限FM2四股10/16保存結果；完整原件、投影、PNG與新私人HTML均留Git外。公開示範僅合成資料，public real-verification只含計數／指紋，不含價量。

正式false、NOT_VALIDATED、主壓力null、1101及70／2／其中8／真實合格0保持。沒有股票分數、推薦、勝率、買點或資金比例。OBS1實機／正式私人網址／全市場私人批次仍分開未驗。Oracle、VPN、部署與日排程繼續暫停；本輪交付後停止，等待總監及使用者回饋，不自啟策略或下一工程。
