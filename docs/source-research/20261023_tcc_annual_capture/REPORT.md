# 本輪實際歸檔報告

## 已完成範圍

原環境恢復至spec8／observed8、connected/running，exec命令實際可用；status的network policy state仍unknown，沒有冒稱enforced或全部入口通行。未改環境設定、代理、CA或TLS。遠端指定分支71e6ff26及三指定祖先已核，main仍9c5b168c09ba80010c74f03b9c537e8b7474256a。本輪唯一Codex處理，未啟動平行工作或子代理。

按AGENTS重新bootstrap --hydrate-missing成功，0補缺／7差異保留，再進行來源歸檔。精確新URL一次GET，HTTP200，無轉址／重試；原件4,932,379 bytes，SHA 7406e30d1f02f083611f594459b952494816d87237bf2203734ce6afb487155d，Git blob f6d87f6ee476c56cb596a4d6fa326d8a45ac85ba均匹配Work參照。完整Git追蹤HEAD原無該blob或同大小檔。新Codex捕捉2026-10-23T17:18:18.708199+00:00～2026-10-23T17:18:22.478497+00:00，與Work16:50捕捉分開，Workmeta未取得不冒已交付。

## 指定四頁實際核讀

| 物理／印刷頁 | 真實觀察 | 日期／對象／精度限制 |
|---|---|---|
|52／102–103|右頁115/1/13董事會通過註銷第七次買回庫藏股暨訂定減資基準日案|只有會議日，不是已證基準日|
|58／114–115|註14寫28,000,000股及115/2/23經授商字第11530011800號函核准|公司報告核准函；函原件未取得，不借作生效日|
|57／112–113|股本形成表115.03、其他欄(280,000,000元)、註14|月份不造精確日，金額不是個人退資|
|60／118–119|第七次已辦理銷除及轉讓之股份數量28,000,000股|同家族交叉來源，不新增事件或樣本|
|57／112–113|普通股7,523,181,742、特別股200,000,000；形成表實收7,723,181,742|不同表及股別口徑分開，不將實收總數當普通股或個人權利|

PDF總113頁；只視讀上述四頁指定項目。物理58註14的native line48、物理57年月line113及金額line112，物理52會議主題line50／日期line61為合併儲存格，以圖核關聯，不單憑文字先後配日期。物理60第七次欄及銷除列line32／57同樣以圖核對。

舊財報本機重用：PDF3320224 bytes／SHA e8a8ca682a242180a908a68030dc80ee0321ddf92217586f59230b1d3e584d2d，原native實體52為115年1月辦理註銷28,000仟股、57為本期註銷28,000（仟股）。本年報表列115.03與該月份差異未調和；不選任一作生效、不拆兩事件。舊PDF／meta／native／圖完全保留，沒有重抓重畫；定位見observations.json。

## 實際檢查與警告

pdfinfo return0／stderr0；pdftotext return0／完整stderr7992 bytes、222行 `Syntax Warning: Invalid Font Weight`；四個pdftoppm各return0／同警告2行。全部新stdout／stderr及PNG指紋保存；Work原完整stderr未交付，不冒已取得。新警告不證舊Fontconfig／xref已消除。離線verify_archive.py已實跑PASS，只核原件、meta、處理檔與圖指紋、盤點界線；新來源封包CRC／manifest與解壓檢查另見delivery/package-verification.json，**不是產品測試**。

沒有新產品模組、catalog／0.11、帳務事件或獨立樣本；沒有執行producer、資格重算、產品／歷史回歸、daily／journal、六方案或Android。不以歷史53、70／2／8／合格0作本輪結果。舊Work ZIP及meta／研究檔未取得未讀未驗；公司新聞中英文重複／嘉新讀取逾時只使用者提供Work結果，本Codex未發新請求或取得該候選。

## 日期、來源及未完成

年報3/24截至時點不等公告，PDF建立5/12 06:13:56Z／修改06:27:10Z、HTTP Last-Modified亦不證歷史截止可得。announced_at／actual_effective_at保持null，核准函原件缺；1月／3月差異仍未解。其他完整行動／區間權息、直接復牌／可交易、個人實配畸零／既有2884換股影響、台泥最後調整／最細稅源、個人淨分配及九起點權利仍缺。

原0.10與全部parent null、catalog、引擎策略、庫、Raw null／UNKNOWN、歷史、原件與成品不改。三根交接僅新增前綴，逐檔保留核對見preservation.json；main未變。固定來源提交逐檔GitHub原bytes讀回後才報交付，收據在delivery，避免自指SHA循環。

未取得：經濟部函、Work原meta／頁圖／完整研究與舊包；未讀：未取得資料及非指定109頁之視讀；未實作：產品接入／0.11（不在範圍）；未執行：producer／資格／每日帳／六方案；未測：產品回歸／Android；未讀回：Work原封包，這與本Codex新來源固定逐檔讀回分開。

下一步只交Work唯讀來源研究；完整可貼文字見WORK_HANDOFF.md。優先用庫內原件及真正新線索，不反覆核同檔、不重問已答比例、不造績效、不公開私人原件、不重試既錄拒絕入口或嘉新逾時路徑。不部署、付費、交易、訊息或子代理。
