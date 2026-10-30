# 台泥114年度年報：新Codex來源歸檔

這是來源歸檔，**不是0.11、帳務事件或產品接入**。原唯一Codex於環境恢復後接續；遠端71e6ff269b0ed974a3b7cfe97c3fdd3d5e9d66b2及指定祖先已核，全部後續與main保留。

- [原PDF bytes](raw/tcc-annual-114.response)（可用PDF閱讀器開啟或另存.pdf），4,932,379 bytes；SHA256 `7406e30d1f02f083611f594459b952494816d87237bf2203734ce6afb487155d`。
- Git blob SHA1 `f6d87f6ee476c56cb596a4d6fa326d8a45ac85ba`。與使用者提供的Work比對值一致；這是本Codex新捕捉，不是Work原meta／研究包已交付。
- [公開安全meta](raw/tcc-annual-114.meta.json)：精確URL一次GET、HTTP200、未轉址／未重試；開始2026-10-23T17:18:18.708199+00:00，完成2026-10-23T17:18:22.478497+00:00。標頭為解析後公開安全欄位，不冒原始header bytes。
- [人工視讀及圖指紋](visual-review.json)、[公司來源觀察](observations.json)、[日期角色](date-roles.json)、[完整處理診斷](pdf-processing.json)、[範圍／未完成](availability.json)。
- [物理52／印刷102–103](visual/tcc-annual-114-p52.png)、[57／112–113](visual/tcc-annual-114-p57.png)、[58／114–115](visual/tcc-annual-114-p58.png)、[60／118–119](visual/tcc-annual-114-p60.png)。只實際視讀這四頁指定項目，非113頁全書核閱。
- [報告](REPORT.md)、[契約界線](CONTRACT.md)、[完整Work唯讀續接指令](WORK_HANDOFF.md)、[來源交付包及固定讀回](../../../deliveries/m1-tcc-annual-source-20261023/README.md)。

## 核讀結果與差異

115/1/13是董事會議日；115/2/23是**公司年報報告**的經濟部核准函日期，函原件未取得；股本形成表115.03保留月份，不能當精確生效日。年報28,000,000股與舊第二季財報28,000仟股只作同家族交叉來源，新增帳務事件／獨立市場樣本0。

舊財報「115年1月辦理註銷」與本年報股本形成表「115.03」分開留存，不自行調和、選日期或拆成兩事件。actual_effective_at及announced_at仍null。普通股來源表7,523,181,742股、特別股200,000,000股與股本形成表實收7,723,181,742股口徑分開；不把含特別股的總數直接當普通股或推個人權利。

## 使用及診斷

離線檢查此來源歸檔（只需Python標準庫，不重新下載或轉圖）：

```bash
python3 verify_archive.py
```

來源處理pdfinfo／pdftotext及四頁pdftoppm均return0。pdfinfo stderr空；pdftotext完整stderr7,992 bytes、222行Invalid Font Weight警告；每頁轉圖各2行同警告，完整stdout／stderr均在raw。新完整stderr是本Codex新產物，不冒Work原stderr已取得；不證舊Fontconfig／xref消除。

bootstrap成功0補缺／7差異保留。離線來源／封包檢查不是產品測試；沒有重跑producer、資格、產品／歷史回歸、每日帳、六方案或Android。原0.10全部parent、策略引擎、庫、Raw null、UNKNOWN歷史、catalog、舊頁／原件／成品與main不改；不回寫parent null。

全部來源缺口及execution_qualified=false、imputed_close／valuation=null、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false保持。日期元資料不證歷史公開可得；公司註銷不自動等於股東比例減資／退資。私人原件不公開、不補零或行情。不重試既錄拒絕入口、library、已存CTBC／受限公開說明書／嘉新失敗路徑，不以unrestricted解禁。不部署、付費、交易、訊息或子代理。
