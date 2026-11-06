# C原單遭拒後再次重評：入口

純API：`conditional_retry.retry_rejected(request)`。只接一份已保存review0.2的C拒評原件，追加一次當期重評；不自動循環、不選數量、不建立新單。

- [恢復資格後原單買20：白話摘要](readback/qualification-restored.txt)、[完整actual](initial/qualification-restored/actual.json)。
- [仍UNKNOWN：原單未買，依原期限到期](readback/still-unknown.txt)。
- [原單只買7，剩13依原期限到期](readback/partial-seven.txt)。
- [當期撤銷：不買且保留第一次拒評](readback/currently-revoked.txt)。
- [較晚啟動前限制生效：明示未支援](readback/limit-before-activation-unsupported.txt)，僅顯示停止前歷史帳，不當成功延續。
- [報告](REPORT.md)、[事前契約](CONTRACT.md)、[首16案索引](initial/summary.json)、[補充歷史篡改拒絕](additional/summary.json)、[新批觸發對照](new-batch/summary.json)。
- [7方法首次log](tests.log)、[READ版本防線補驗2方法](tests-READ-schema.log)、[自審](self-review.json)、[提交檔案指紋](CHANGE_MANIFEST.json)。7唯一方法／9次執行，不加歷史PASS或17案例數。

本輪`initial/`即最終數值source結果；之後只增READ schema防線，數值source未變、未重跑16案。`additional/`是另先凍結再執行的第17案。範例精確輸入／預期在`cases/*/`，來源及凍結指紋在`intake.json`、`history-tamper-intake.json`；所有舊原件未改。

成功範例保留第一個REJECTED receipt，再加一個ACCEPTED receipt，原r1-B只新增買20；原資本1430、權利及reserve100保持。新買20是原單remaining，不是新的一批。新批仍須新獨立觸發；[對照](new-batch/expected.json)只驗資格，沒有新批委託／成交或1/13行情。

直接唯讀已有結果：

```bash
cd /workspace/Twstockai/股票系統M1_v0_18
python3 -B -m capital_research.lifecycle_read \
  capital_research/c_order_retry_20261027/initial/qualification-restored/actual.json
```

READ無引擎／寫入／網路。新的retry則是使用者明示的合成RUN，為核對原始quantity閘門與歷史，會用原輸入重建一次原0.2結果，再委派原執行引擎接續；不改寫該原件或冒稱READ。新輸出review0.3，原決策／執行0.9、checkpoint0.8、scope0.1不改。所有數字合成、正式資格false／主壓力null，非市場績效。
