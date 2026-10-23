# 公司行動決議來源與每人總額圓整 0.4

承接遠端 `d11cd18a53d688eae4602461392a6602313cea9f`，保留9e41ea3及後續Work來源補核。新純數值 `action_resolution.py`、外部離線 `action_resolution_sources.py`；原0.3與全部舊程式／策略／庫／成品不改。

台泥2026/5/22通過決議以新來源版本接入，原提案版本完整保留；每人現金總額圓整只產生明示假想權利股數的毛額預覽，淨額／稅費／實際到款仍null。庫藏股第六／七次報告只是公司層級來源盤點，不能變成股東減資帳。

- [契約](CONTRACT.md)、[完成與限制](REPORT.md)、[完整續接](WORK_HANDOFF.md)
- [新catalog](events-v04.json)、[資格](window-qualification.json)、[假想毛額](gross-previews.json)
- [本輪定向測試](tests.log)、[來源與資格實跑](verification.json)、[輸出與保存核對](output-verification.json)、[保存](preservation.json)
- 新封包及GitHub固定回讀：根 `deliveries/m1-action-resolution-20261023/`

完整checkout先在根重新bootstrap，成功後進入股票系統M1_v0_18：
```bash
python3 -m unittest rotation_research.test_action_resolution -v
python3 -m rotation_research.action_resolution_sources
python3 -m rotation_research.package_action_resolution
```

新29測試通過；70窗實跑仍拒算、2不足、總淨報酬合格0。無新六方案績效。下一步Work補可核來源；已定工程再交Codex。
