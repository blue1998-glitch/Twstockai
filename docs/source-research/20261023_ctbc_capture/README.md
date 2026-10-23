# CTBC代理公司股利表：Codex新捕捉與交叉佐證

原唯一Codex接續773b13b384ae302851801affa4c2ca5e78ee2a7f，核包含固定0.10 f423447c9396bfdd7c524f4c5f63173be1ebb47d及所有後續。使用者明示環境已發佈並授權精確CTBC URL單次GET後，先核runtime由spec4變spec6／observed6、observations_current=true、unrestricted/enforced，再實際取得HTTP200；沒有改設定、跟轉址、額外請求或重試其他受拒入口。

## 實際原件

- URL：https://ecorp.ctbcbank.com/cts/static/ag_dividend_printer.jsp
- 原始bytes：647329。
- SHA256：`ac8340b658018958e500f576bdc7605475cea0f48dac010e2c5251a1750aa310`。
- 開始2026-10-23T14:55:50.627058+00:00，完成14:55:54.015924+00:00（台北22:55:50～22:55:54）。
- [原始表格bytes](raw/ctbc-dividend.response)、[本輪meta](raw/ctbc-dividend.meta.json)、[四筆來源選列](ctbc-dividend.selection.json)、[工程實益核對](engineering-assessment.json)。

大小及SHA與使用者提供的Work參照相符，這是本輪新Codex捕捉，不是Work研究ZIP接入。Twstockai-v010-Work-source-handoff-20261023.zip、MANIFEST、WORK_RESEARCH_HANDOFF全文及Work meta／selection仍未取得未讀；沒有重試chatgpt library。工作模式的捕捉時間不借作本輪時間，work_github_readback_at及announced_at保持null。

原HTTP回應帶Set-Cookie；原meta保留於本機非Git路徑且權限600，公開meta明示遮蔽該值，其他標頭保留。原HTML bytes完全不變。公開meta的指紋只代表已遮蔽版本，不冒完整原header bytes；沒有將會話cookie寫入GitHub或來源包。

## 原表核對

表題「最新代理公司除息(股票股利)一覽表」，製表115/09/18（2026-09-18）。六欄依序為證券代號、公司名稱、每股現金股利（元）、除息交易日、最後過戶日、發放日。

| 代號 | 原表金額（元／該證券每股） | 除息交易日 | 最後過戶日 | 發放日 | 原HTML起始行 |
| --- | --- | --- | --- | --- | --- |
| 1101 | 0.8 | 115/07/01 | 115/07/02 | 115/07/28 | 84 |
| 1101 | 1 | 114/07/02 | 114/07/03 | 114/07/29 | 124 |
| 1101B | 2.0262 | 115/07/01 | 115/07/02 | 115/07/28 | 164 |
| 1101B | 2.0262 | 114/07/02 | 114/07/03 | 114/07/29 | 204 |

以原件UTF-8、HTMLParser實讀六欄，並人工核原HTML四列與表頭；不是將使用者摘要填成已核原件。金額保留decimal字串及公開小數位，年度只由除息交易日得到「交易曆年」，不是表內不存在的盈餘年度。1101普通股及1101B乙特分開，乙特金額不覆其他來源更精確金額。

## 工程實益結論：只歸檔，不建0.11

兩筆普通股的金額、除息日、公司發放日期，均與原action_resolution_20261023/events-v04.json的既有兩事件一致，已逐欄連原event ID及source檔SHA。CTBC新增交叉來源與最後過戶日觀察，不解除既有淨帳缺口，不需改目前產品程式。兩筆乙特只存旁證，未套入普通股帳。新增帳務事件／獨立市場樣本0，不改任何catalog或parent null，沒有新產品規則／策略或0.11。

最後過戶日不是除息基準日、公告日或個人到款；原record_date維持null。製表日不是公告或區間完整覆蓋證明，捕捉不能倒填announced_at。公司排程非個人淨入帳／實配或權利證明。起日前除息涉及期初應收權利，不自動歸給起日後持有人。原件沒有2884列只描述此代理表，不證2884無事件或全市場完整。

## 驗證與使用

重新bootstrap成功0補缺／7差異保留。只有來源檔SHA、完整六欄／四列、日期角色／字串精度、舊事件交叉及原成果保留核對；這些是來源歸檔檢查，**不是產品測試**。沒有重跑歷史53、產品回歸、producer／資格／每日帳／六方案或Android，不能將歷史70／2／8／合格0寫成此次新跑。

離線核來源包，不需要網路、瀏覽器或額外套件：

```bash
python3 verify_capture.py
```

腳本只核新來源的原bytes、選列、meta與界線，不匯入或改產品引擎。結果見source-verification.json。來源小包／SHA／manifest、全新解壓重核及固定逐檔GitHub原bytes讀回見 [delivery](../../../deliveries/m1-ctbc-source-corroboration-20261023/README.md)。這不是完整專案包，勿覆寫原專案；查看selection JSON或以文字檢視原HTML即可，不重試file://政策或外載銀行腳本。

原0.10所有來源契約、Fontconfig勘誤（五頁return0但表決頁有快取警告）、PDF／JSON／PNG／catalog／ZIP與舊xref歷史不改不重抓。完整行動減資／區間權息、直接復牌／可交易、個人實配畸零、既有2884換股影響、台泥最後調整／最細稅源、個人淨額與九期初權利仍待來源。不假定無事件、不補零、行情、前價或估值，不公開私人原件。

execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。全換／分批研究資格、Raw／五年Adjusted／歷史公布／主檔／SQLite未知保持。沒有新UI／Android，不部署、付費、交易、發訊息或子代理。下一步Work只唯讀檢查本輪來源與未解缺口，完整可貼指令見 [WORK_HANDOFF.md](WORK_HANDOFF.md)。
