# 官方公司行動來源補充 0.2（2026-10-22）

本輪新入口。保留舊事件帳0.1、來源日曆0.1、P1-7、舊成品及main；只新增官方文件擷取與獨立離線來源補充。沒有新增UI。

- [實測與資料限制](REPORT.md)
- [欄位／時間／資格契約](CONTRACT.md)
- [新事件表](events-v02.json)：僅補強原2884股票股利組件，不是新增公司事件或完整行動名冊。
- [官方原件及衍生文字指紋](source-manifest.json)、[議事錄事實](minutes-facts.json)、[公司完成報告](completion-facts.json)。
- [70窗口仍拒算](window-qualification.json)、[實際執行摘要](verification.json)、[17測試紀錄](tests.log)。
- [完整續接／回Work指令](WORK_HANDOFF.md)。小ZIP及GitHub回讀見根deliveries/m1-official-actions-20261022/README.md。

可離線執行（標準Python，不連網、不重跑原策略）：
```bash
cd 股票系統M1_v0_18
python3 -m unittest rotation_research.test_official_actions -v
python3 -m rotation_research.official_actions
```
PDF原件及pdftotext衍生文字均已封存，離線producer只讀經SHA綁定的文字，不需安裝PDF套件。若要獨立重做抽字，依raw/*.extraction.json的命令用pdftotext；後續執行producer不會自行連網或覆寫舊結果。
