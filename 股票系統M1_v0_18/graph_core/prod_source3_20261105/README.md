# M-PROD-SOURCE3｜安全Range已交付；完整新正文為11/5，未通過本輪日別資格

同一正式產品 **http://127.0.0.1:8765/** 仍顯示11/3，1986終態（1955歷史不足／31來源拒用）。這是Cloud本機入口，Android外部未連通。**本輪更新股票0／新核心0／新Journal0，沒有新日發布**；不能把傳輸完整或測試PASS當日更成功。

## 真實請求與精確原件

從原兩份partial實際讀bytes、長度與SHA，核最長4,570,729 bytes、總長5,329,099、缺758,370；弱ETag／版本衝突／前綴不一致均拒絕。原強ETag `"6aec6fc6-5150cb"`，原Last-Modified12:00:06Z。只送一次原URL的 `Range: bytes=4570729-`＋`If-Range`，沒有Range迴圈或第二次主來源請求。

伺服器實回**HTTP200完整新正文**，5,329,099 bytes、SHA256 `90417d229be64406bc7ac59a858093445746d4d4a47f9b098c37e4ac687e2e54`；ETag已變 `"6aec8be8-5150cb"`、Last-Modified14:00:08Z。依HTTP語義以獨立完整body保存，**舊prefix使用false，沒有混接**。這不證Range不支援，也不宣稱實際206續傳成功；只能證If-Range沒有提供舊物件尾段。本次完整傳輸已成功，不能繼續沿用「仍截斷」作為當前唯一阻礙，舊EOF所在hop仍未定位。

原官方quote_map解析完整正文，唯一Date為**2026-11-05**、原始證券資料13,679列（不是普通股數，也未跑全體OHLCV品質／CFI）。舊partial的完整資料日期未採信，不能因本輪目標11/4便稱舊body已證11/4。已保存的上市完整件是11/4，兩者不能拼成同日六件。

Issue #6允許的唯一替代檢查使用同官方 `tpex_mainboard_quotes`，HTTP200完整1,017列，Date也是**11/5**；原必需欄位都有，但名稱相同不自動證股數單位、ISIN/CFI或新資料集資格。**日期不符已足以拒用**，未正規化、未補值、未把1,017列當普通股母體。只是Issue明示的一次私人檢查，沿用原TPEX OpenAPI私人非商業範圍，不假稱另取得原始授權文本或公開散布權，不重試舊403 data.gov入口。

## 日別停止條件與保全

已用完本輪主來源1次＋替代1次。分類GET0，不再抓其他來源。實際台北時間22:22的原`prod_core1.flow.fetch(2026-11-05)`在任何GET／stage寫入前返回原有 **PRIOR_CLOSED_DATE_ONLY**；沒有改時鐘、放寬當日完結／公布資格。完整11/5上櫃原件保留獨立candidate descriptor，上市同日件與分類未取得，不能稱11/5完整批次。

同一owner已讀最新日期不符原因；原11/3有效head逐bytes相同，401認證保持。舊11/2、10/30、全部FM3/帳務/原件與來源parents未改。原目標11/4來源不足、11/5受既有時間及六原件閘限制，**來源操作到此停止**。只有等原日期條件允許後，才由總監續派補齊已保存11/5原件的同日雙市場六件並接原掃描／Journal；不再追無版本端點的舊partial，不自行等候輪詢或發新GET。

## 可重用工程與必要驗證

`resume.recover(prefix,proof,opener)`只允許一次原URL請求。206先核Content-Range起訖／總長、強ETag、Last-Modified與片段宣告長度，再核實得長度、完整拼接SHA／讀回；200則獨立正文。416、403/429、跳轉、版本不符、任何截斷均拒用，沒有force或降低TLS／proxy限制。原receive預設仍只接受200；206只由本安全caller明示允許。原quote_map及下游全部來源／日期／公司行動／價基底閘不改。

維運入口：原Cloud先核當前身分及engineering.lock，再透過`codex/unified_workspace.py --run`執行：

```text
python3 -m graph_core.prod_source3_20261105.resume
python3 -m graph_core.prod_source3_20261105.alternative
```

**本輪兩份結果均已存在，再執行只讀原結果**。marker有而結果無則拒絕未知中斷，不重送。禁止刪marker、換工作目錄或改名來擴張本輪額度。完整body／片段採原DU2 exact-byte codec，與原SHA一致；只新存小型依存，原bytes不覆寫／搬移。沒有另一資料庫、網站或金融引擎。

10唯一Python方法PASS（中間7／8不累加）：合格206、200不混接、錯範圍／總長／ETag／日期／長度、弱與衝突前綴、403/429/416/跳轉、截斷、預設reader拒206、替代日期／缺欄不補值、快取零請求。206只是工程HTTP-parser fixture；真實是完整200與兩來源日期。真實重送GET0／新增檔0；原當日日期閘實測0GET／0新檔；owner HTTP根入口／status／401通過。前端未變，不重跑舊26瀏覽器或1955核心；Android本人未測、外網未連、排程未啟。

[summary.json](summary.json)、[verification.json](verification.json)、[tests.log](tests.log)為不可還原公開證據。真實原件與完整分析不進Git。驗收時FS淨增950,272 bytes、free559,226,880 bytes，仍保留至少536,870,912；FM3 metadata90377沿用原SHA審計加不變metadata，沒有重做19GiB全量Hash。880歷史untracked、main、私庫bridge、UNKNOWN／false/null與正式策略限制全部保持，獨立備份與重啟持久性仍UNKNOWN。

正常提交與固定GitHub逐檔原bytes讀回後停止；收據另存避免自指。沒有Oracle、Android新網路、外部部署、付費、排程或交易。本輪不是日更成功，也不延伸為新的策略或來源大研究。
