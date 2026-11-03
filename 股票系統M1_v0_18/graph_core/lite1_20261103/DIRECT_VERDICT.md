# M-LITE1直接判定介面補充

沿原同一工作台／owner入口 http://127.0.0.1:8765/，本機已驗新版可操作；沒有另建UI或新里程碑。這是原Cloud本機入口，不是新Android外連網址。

## 已接上的直接判定

- 列表及雷達：股票＋原判定先顯示，關鍵價、量價狀態與限制接在下方；同股原候選仍收折。多股比較第一眼同樣是判定／關鍵價／量價／限制。
- **圖內真正畫出五行**：目前、關鍵價、量價、風險、參照；不只放在圖外說明或ARIA。量價明寫「未判定」及原較前筆量觀察，不把量增當配合或量少當壞。
- 價格線在原精確價格；單一可追溯研究點用原日期／原價位畫點、連線短標籤與完整年份，並提供「看參照點」。定位／移圖／縮放不改分析日。來源在圖外不偽畫在今日，超價軸不強拉入軸。
- 多點、多價位或研究箱起日不冒唯一原高點；未核定主參照明示「未指定主要點」。同位置多ID仍全部保存在證據；無當期過線參照不抹掉原可比較研究，只顯示未指定當期參照點。
- 圖內短句有獨立86px顯示區，原主圖畫布增高60px並等距下移原三面板；K／量／MACD面板原高度與共軸仍保留，沒有用小字或遮住K線換空間。原viewer來源不改，只在此既有輕量renderer複本做可核對的顯示位移。
- JSON／來源ID／候選／SHA仍在明示展開的技術明細，下載保留原完整精度與來源。

沒有批准的量價配合、正式結構失效或主壓力算法，**不會為填滿介面而發明判斷**；量價確認及primary_pressure_id仍null。圖上「非主壓力」是研究參照資格。原突破／回區間／跌破事實保留，不能被量觀察抹掉；不產生買賣、勝率或報酬承諾。

## 本輪實測

9唯一Node純呈現方法；16組真實Chromium＝三尺寸各5組＋390寬多參照反例1組；6次精確原JSON下載（2保存股／日×3尺寸，不是6市場樣本）。另4項實際owner HTTP控制。沒有重跑或加總舊17 Python／5 Node／34瀏覽器、原31／28或全市場核心。

真實保存案例包含：11/02分段不可判定、10/30一個可追溯原參照點，以及多參照分歧。個股／日期／價格由既存小型判定分片挑選驗收案例，沒有寫成生產常數。合成時間／缺參照／同價異日／研究箱非pivot等反例另列純方法，不當市場樣本。三尺寸PNG、原配置與全部前後版只Git外 `lite1_20261103/direct-verdict/`（最終版在final/browser）。第一輪視讀將月日補完整年份、並區分無新事件參照與無可用參照，重測同方法不加總。

最新HTML **1597512B（約1.52MiB）**，初始仍0事件／0原圖；已驗目錄下冷Chromium0.769秒／JS heap約4.61MiB。owner首次新目錄驗證另需數十秒，非Android效能保證。本補充所有試作／PNG／驗證FS淨增8.10MiB，驗核餘707.73MiB，高於512MiB；本輪上限16MiB。沒有重建分片或複製原圖，先前M-LITE1各次預算／數字留史，不清掉舊版迎合首輪總額。

兩日期完整保存market-state原bytes相同（1986身分、原判定、事件／價格精度與路由），asset manifest SHA不變；source head小檔SHA相同，原90377來源路徑metadata沿既有全量指紋。原core／MA／MACD／reaction_facts／P0-3／OBS1／COMP1及owner驗證來源未改。沒有新行情或核心／指標計算。見[驗證與保全](DIRECT_VERDICT_VERIFICATION.json)、[實際瀏覽器](DIRECT_VERDICT_BROWSER.json)、[效能](DIRECT_VERDICT_PERFORMANCE.json)、[純方法日誌](direct-verdict-tests.log)。

## 交付邊界與接續

公開GitHub只程式、合成控制及不可還原摘要；原件／完整行情／JSON／HTML／PNG／憑證維持Git外。來源0.10／parents、Raw／UNKNOWN、正式false／主壓力null、全部歷史、原頭與main不改。Android新版實機未測；Oracle／新外部入口／日排程未啟，獨立備份與重啟持久性仍UNKNOWN。原SIGKILL／SQLite／xref／Fontconfig／file://及受拒入口未動，不造淨帳／六方案。

本輪固定工程／讀回見DIRECT_VERDICT_READBACK.md與JSON，收據另提交避免自指；下方既有成品與收據皆保留。完成後停止。

可貼Work：接續blue1998-glitch/Twstockai的dev/m1-v018-chart-annotations，先唯讀核最新HEAD及77591f9祖先，讀根最新節、本DIRECT_VERDICT、verification／browser／performance及DIRECT_VERDICT_READBACK固定SHA。只檢視直接判定與原研究真相是否一致；原主圖及分片已接上，不另做UI、策略或來源研究，不重跑歷史驗收、不冒實機通過。Work若不能讀原Cloud私人PNG，明列未取得未讀，不以摘要冒原件、不要求手機搬檔。不重問已答規則；沒有新使用回饋就停止，不另派工程。Oracle等明示帳戶完成及授權。
