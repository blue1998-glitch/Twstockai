# 獨立來源研究附層0.8：契約、適用持有人與增資組件

入口：[CONTRACT.md](CONTRACT.md)、[REPORT.md](REPORT.md)、[WORK_HANDOFF.md](WORK_HANDOFF.md)。純事實核心 `../source_contracts.py`；離線producer `../source_contracts_sources.py`；新測試 `../test_source_contracts.py`。

精確嵌入完整0.7，parent_catalog_id=`sha256:49528167bede030b29359a77abebd3f8947c88e58aeaaeede62c42a76465cc89`。所有舊版本、核心／策略／參數、庫／Raw／歷史／原件／舊頁／成品與main保持。新7筆是不同角色來源觀察，不是7個獨立公司行動，也不是個人權利／正式策略。

實際重用原公開說明書14,607,733 bytes，SHA `926f1f871a294702d3e4f5e4d89cf5aeb5e64808593efa2d99b95ed7375388fa`，另從固定6a993fd GitHub回讀同bytes；本輪只視讀實體頁162／163／175／176／461，765頁未全書視讀，xref警告保留。原件及全文native仍在source_diagnostics_20261023/raw，不複製覆寫。新2026Follow-up.pdf精確URL只GET一次HTTP200，56,705 bytes／SHA `02899d55a0ce5431e3ec9787652a928fd5cc2d35abf56669942db52440e2fcdf`，一頁已視讀。

本環境未見Twstockai-v07-Work-source-handoff研究附件及其meta，未宣稱讀過。依使用者完整文字指令與實際原件完成可確定工程，未要求手機搬檔。Work GitHub讀回時點未知，work_github_readback_at=null；原官方捕捉與本輪Codex讀回另存，不倒填announced_at。詳見handoff-read-inventory.json與source-manifest.json。

在股票系統M1_v0_18執行：

```bash
python3 -m unittest rotation_research.test_source_contracts rotation_research.test_source_followup -v
python3 -m rotation_research.source_contracts_sources
```

本輪31新＋實跑0.7相關29＝60項通過，舊59不冒本輪重跑；全新解壓同60不累加為120。producer離線重核122價量原件與16日曆報告，實算資格仍70拒算／2不足／8換股影響未支援／真正總淨報酬合格0，daily／journal空，numeric replay／六方案0。沒有新UI／瀏覽器／Android驗收。

成品、SHA、manifest、全新解壓及固定逐檔GitHub回讀見 [delivery](../../../deliveries/m1-source-contracts-20261023/README.md)。封包保留原0.7的651成員，解壓到新目錄離線重現，不覆完整checkout。後續工程仍先依根AGENTS重新bootstrap。
