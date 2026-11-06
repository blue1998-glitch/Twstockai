# CTBC新Codex來源交叉佐證包

本輪只新增來源歸檔，不建0.11、不改任何產品引擎／策略／catalog／庫／Raw null／UNKNOWN／歷史／舊成品或main。

- [下載來源小ZIP](ctbc-codex-source-corroboration-20261023.zip?raw=true)：34,078bytes、14成員、13項manifest。
- SHA256：`4617406c67f1c70898561ebbc81b3e303c9e640c7715bf1d57a5479560e71cb6`，另見[SHA256SUMS](SHA256SUMS)。
- [取得與來源範圍](../../docs/source-research/20261023_ctbc_capture/README.md)／[實際公開meta](../../docs/source-research/20261023_ctbc_capture/raw/ctbc-dividend.meta.json)／[四筆選列](../../docs/source-research/20261023_ctbc_capture/ctbc-dividend.selection.json)。
- [工程實益判斷](../../docs/source-research/20261023_ctbc_capture/engineering-assessment.json)：普通股兩年金額、除息及公司發放日均與既有事件相符，只需來源交叉佐證，不新增事件或獨立市場樣本。
- [來源包新解壓核對](package-verification.json)／[離線執行紀錄](extracted-verification.log)。CRC、安全唯一成員、全部manifest及原件SHA通過；解壓後python3 verify_capture.py通過且所有成員bytes不變。這是來源檢查，產品測試0。
- [完整Work唯讀續接指令](../../docs/source-research/20261023_ctbc_capture/WORK_HANDOFF.md)／[固定逐檔GitHub原bytes讀回](GITHUB_READBACK.md)／[JSON](GITHUB_READBACK.json)。

使用者發佈環境並明示新授權後，先核runtime spec6／observed6、unrestricted/enforced，再對精確CTBC URL一次GET，HTTP200、647329bytes、SHA `ac8340b658018958e500f576bdc7605475cea0f48dac010e2c5251a1750aa310`。無轉址、其他來源請求或本輪設定修改。新Codex原件與使用者Work比對值相符，不冒Work ZIP已取得。公開meta遮蔽Set-Cookie值；原HTML bytes保持完整。

原表製表115/09/18，六欄及1101／1101B的114／115兩年度四列實讀核對。年度只為除息交易曆年，不冒盈餘年度；最後過戶日不是基準日，製表不是公告／完整覆蓋，捕捉不倒填announced_at。乙特2.0262不覆較精確金額。公司發放安排不等個人實收，起日前除息權利不能自動歸起日後持有人，表內無2884列不證無事件。

Work研究ZIP、MANIFEST、完整WORK_RESEARCH_HANDOFF、Work meta／selection仍未取得未讀，library未重試。這個ZIP是本輪Codex新來源包，不是Work交接ZIP或完整專案包，勿覆寫專案。全新目錄解壓後可離線執行：

```bash
python3 verify_capture.py
```

本輪bootstrap成功0補缺／7差異保留，僅來源與歸檔核對；沒有新產品測試／回歸、producer／資格重算／每日帳／六方案或Android，歷史53及70／2／8／合格0未冒本輪重跑。所有來源不足及資格旗標保持，不部署、付費、交易、發訊息或子代理。
