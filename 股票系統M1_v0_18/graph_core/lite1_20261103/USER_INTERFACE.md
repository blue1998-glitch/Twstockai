> 2026-11-03 直接判定補充：圖內五行判定、原參照點與量價未判定已接上，最新成品與實測見 [DIRECT_VERDICT.md](DIRECT_VERDICT.md)。下方原版數字／驗收留史，不當本輪重跑。

# M-LITE1 使用者導向補充，仍是同一工作台

本輪依使用者「原頁已可開啟操作」回饋改善呈現，不是新里程碑或第二套UI。沿原Cloud、原owner入口 **http://127.0.0.1:8765/**；本機新成品已驗。使用者原回報不冒充這次新版Android實機驗收，也沒有新外部網址／Oracle部署。

## 現在的操作

- 首頁先見資料日期、非即時／較早批次、保存圖涵蓋範圍、市場觀察短句、事件分類與搜尋。可在頁首「換日期」，不必捲到底找入口。
- 股票卡片顯示代號名稱、當期原判定、原參照價、量觀察與短限制；「看走勢」開原圖，「加入比較」並排看。移除主畫面候選票數，不刪原證據。
- 雷達按股票顯示；分類用繁體中文，股票數與參照事件數分開。首次研究觀察日不是公告日；篩選舊事件時仍明示卡片分析日。所有事件分類保留，可在有界區域滑動選擇，不做重要性排名。
- 比較頁在手機是逐股字卡，桌面沿原表格；代號名稱、目前觀察、參照價、量與限制先顯示，每股有自己的看圖／移除按鈕。原COMP1 scope完全不改。
- 說明頁先顯示短句，原JSON／來源ID／SHA／基底／批次工程資訊只在明確展開的「進階技術明細」。日期選單不再露內部run ID；原白名單連結與SHA檢查照舊。

「新舊資料無法連續比較」「歷史不足」仍可見；沒有改成買賣、趨勢反轉或通過資格。11/02仍保留原不可判定／不足，不因文字變白話就提高研究真實性。價格字串完全保留精度，量仍只較前筆，未知不補零。

## 本輪實測與原件

新版11/02 HTML **1594562B（約1.52MiB）**，初始仍0事件／0個股圖。owner目錄已驗證後，390寬冷Chromium首次傳輸1596163B、等待0.763秒、JS heap約4.61MiB；本機單次樣本，不是Android效能保證。切換新目錄驗證及服務首次啟動仍約數十秒，未把暖機成本隱藏成0.763秒。

補充含所有試作、圖及驗證的FS淨增 **15.59MiB**，驗核剩716.30MiB，高於512MiB，預先上限24MiB。沒有重建分片或複製1946份圖。原M-LITE1兩日期完整market-state腳本的 **原bytes完全相同**，含全部1986身分、判定、精度、來源、分片路由；asset manifest SHA相同。原M-DAY1／FM3兩head小檔SHA相同，沿用原90377路徑metadata與前次全量指紋，不重驗19GiB。見[PRESENTATION_PRESERVATION](PRESENTATION_PRESERVATION.json)。

實跑17唯一Python＝2日期呈現＋8原白名單＋7owner安全回歸；5個Node純呈現方法；34組真實瀏覽器＝24三尺寸完整流程＋7定向邊界＋3最終版分類區高度／捷徑控制；5數值下載原物件相同、6個實際owner HTTP控制。前輪31Python／28瀏覽器沒有冒本輪重跑；中間重試批不加總。詳見[PRESENTATION_VERIFICATION](PRESENTATION_VERIFICATION.json)、[瀏覽器](PRESENTATION_BROWSER.json)、[邊界](PRESENTATION_EDGES.json)、[捷徑](PRESENTATION_SHORTCUTS.json)、[效能](PRESENTATION_PERFORMANCE.json)及兩份presentation-tests日誌。

最後僅加分類區高度、提示字與「暫無圖可看」中性摘要，沿同UI／資料／路由，重新驗三尺寸全部分類可達與日期／搜尋；沒有新增圖形或事件規則。手機直橫與桌面圖片在Git外 `lite1_20261103/presentation/final/browser`（字卡／圖／舊參照）及 `presentation/delivered/browser`（最終首頁）。原圖與中間版圖片皆留存。

本輪沒有失敗的產品測試；視讀發現日期入口位置／內部批次名及舊日期多分類區過長，於同輪低風險修正。只重啟自己既有只讀owner服務以載入日期文案，維持單一listener；不是重啟Cloud、資料worker或新增對外服務。原SIGKILL／SQLite／xref／Fontconfig／file://及受拒入口不變。

## 保存與接續

GitHub只收程式、合成控制與不可還原摘要，私人行情／完整JSON／HTML／PNG／憑證均Git外。原M-LITE1 readback與manifest保留為固定歷史；本補充另存PRESENTATION_MANIFEST與PRESENTATION_READBACK，避免覆寫原收據或自指。

原核心／MA／MACD、P0-3／P0-4、來源0.10／parents、策略／庫／歷史／main不變；正式false、主壓力／imputed_close／valuation null，Raw／UNKNOWN保持。不重抓資料，不跑日淨帳／六方案。

下一個對象只Work總監唯讀用途檢視：核最新分支包含f890e797，依本補充固定讀回SHA讀本文、verification／preservation／三份browser摘要與收據。不要重算全市場、重抓來源、另建UI或把歷史PASS加總。Work若無原Cloud權限，私人原圖／PNG明列未讀，不以公開摘要冒已驗、不要求使用者搬檔。核對新介面是否看得懂、操作是否順暢即可；沒有新回饋就停止。Oracle、外部Android入口、這次新版實機、日排程、獨立備份及重啟持久性仍未完成／未知，待明示授權再處理。
