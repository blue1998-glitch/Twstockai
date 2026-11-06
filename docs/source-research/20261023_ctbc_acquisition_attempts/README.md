# CTBC研究包及公開URL單次取得結果

由原既有唯一Codex接續af822910278e82a2bf738195411525af8554b08f，先核遠端包含此SHA及固定0.10 f423447c9396bfdd7c524f4c5f63173be1ebb47d，開始時沒有後續。根最新交接、ctbc_intake完整交接及證據、0.10來源契約均已讀。全部舊來源、版本、策略、引擎、庫、歷史、原件、成品及main保留。

## 本輪兩次實際嘗試

按照使用者指定次序與精確URL，各一次GET、不跟轉址、不重試，使用既有代理／CA且TLS驗證保持。兩次都在CONNECT隧道建立時失敗，錯誤皆為：

```text
URLError(OSError('Tunnel connection failed: 403 Forbidden'))
```

| 目標 | 開始 | 完成 | 結果 |
| --- | --- | --- | --- |
| chatgpt.com研究包正式下載網址 | 2026-10-23T14:07:05.601347+00:00 | 2026-10-23T14:07:05.616527+00:00 | CONNECT403，來源HTTP未知、來源bytes未取得 |
| ecorp.ctbcbank.com精確公開原URL | 2026-10-23T14:07:05.616846+00:00 | 2026-10-23T14:07:05.629059+00:00 | CONNECT403，來源HTTP未知、來源bytes未取得 |

精確網址與完整例外／開始完成時點分別在attempts/library-download-attempt.meta.json及ctbc-direct-attempt.meta.json。沒有來源HTTP回應或來源headers可保存，http=null、headers=null；不能把CONNECT403寫成CTBC網站HTTP403或登入驗證失敗，也不能認定來源端已被讀到。

代理失敗時本機工具沒有收到payload，原診斷的0bytes與e3b0…是空buffer指紋，**不是CTBC原件、研究包或服務器回應指紋**；不發布空.response冒充原件。重現腳本僅存本輪實際命令、具已嘗試即拒重跑防護；此處不授權再次執行或繞過拒絕。

當時runtime spec4／observed4且observations_current=true，HTTP模式restricted、state=unknown；回報allowed_hosts沒有chatgpt.com與ecorp.ctbcbank.com。這是設定觀察，未證明所有拒絕原因；實際確認的錯誤只到CONNECT403。本輪沒有改網路設定、主機、路徑、代理、TLS或認證，也沒有請使用者下載上傳。兩個新受拒URL已停止；全部既錄受拒入口仍不重試／繞過。

## 未取得及資格

研究包Twstockai-v010-Work-source-handoff-20261023.zip的28364bytes／SHA 8a095132003632b7497b1ced4566d64bf0c123332d04cc19bc5aa421d0fa2b95，以及Work捕捉CTBC的647329bytes／SHA ac8340b658018958e500f576bdc7605475cea0f48dac010e2c5251a1750aa310僅為使用者提供的比對參照。不能拿這些字串當已取得或已驗封包。

研究包、六成員、MANIFEST、WORK_RESEARCH_HANDOFF.md全文、Work CTBC原件／meta／selection均未取得／未讀／未驗。公開URL的新Codex原件也未取得。使用者提供的製表日期、六欄表頭與四筆1101／1101B列均未從本環境原件核實，沒有產生已核選列JSON或來源facts。

因此來源保存／產品工程實益仍待實際原件核定，不建0.11，不改任何catalog或parent null。可保存的只有失敗診斷及接續指令，不是CTBC來源附層或原件封包。沒有新產品ZIP、每日帳、六方案或新績效。

## 實際檢查及未做事項

文件寫入前重新bootstrap成功：0補缺／7差異保留，見bootstrap.log。已做單次請求錯誤核對、JSON／文件鏈結、Git blob及舊檔SHA保留檢查；不是產品測試。沒有新產品測試／回歸、producer／資格重算、PDF重抓／重抽／重畫、Android或UI驗收。歷史53及70拒算／2不足／8未支援／合格0沒有在本輪重跑或硬編為本輪結果。

狀態詳availability.json。固定文件提交逐檔GitHub原bytes讀回見 [delivery](../../../deliveries/m1-ctbc-acquisition-attempts-20261023/README.md)；文件讀回不能升格成研究包或CTBC原件已讀回。

Fontconfig勘誤維持：五頁舊轉圖return0，但表決頁有快取警告；原PDF／JSON／PNG／catalog／ZIP與舊xref歷史不改、不重抓。子公司IPO方案非完成、場次矛盾及0.10／全部parent契約繼續有效。

若日後實際取得CTBC表，只限公司層級交叉佐證：年度、1101／1101B、對象、日期角色、單位及精度分開；製表日非公告日／完整覆蓋承諾，捕捉不倒填announced_at；2.0262不覆較精確乙特金額。公司發放安排非個人實收，起日前除息涉及期初應收權利，不自動歸起日後持有人；未列2884不等無事件。不重計帳務事件或獨立市場樣本。

完整行動減資／區間權息、直接復牌／可交易、個人實配畸零、既有2884換股影響、台泥最後調整／最細稅源、個人淨額及九期初權利仍缺。缺資料未知／拒算，不補零、行情、前價或估值，不公開私人原件。execution_qualified=false、imputed_close／valuation=null、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false；全換／分批研究資格及Raw／五年Adjusted／歷史公布／主檔／SQLite未知保持。

下一輪不需手機下載上傳，不在本環境重試已拒入口。完整Work唯讀續接指令見 [WORK_HANDOFF.md](WORK_HANDOFF.md)。不部署、付費、交易、發訊息或啟動子代理。
