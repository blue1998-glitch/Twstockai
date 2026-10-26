# 診斷與證據分類

- 本輪新測試集合一次，21唯一方法PASS；build一次，22個預存合成案例符合oracle。沒有失敗批、沒有變更oracle，不需要為取得更多PASS重跑。
- cases/*/actual.json：實際合成診斷輸出，與input／expected和summary指紋綁定；不是行情、帳務或成交actual。
- tests-final.log：21個方法的實跑log；方法內變體不另算唯一方法，也不冒稱每個變體都有完整保存JSON。
- source-versions-before-execution.json：首次診斷前的5個source／contract指紋。verify.py與報告是在執行後新增的只讀審查／文件，以CHANGE_MANIFEST綁定，不冒充當時已執行source。
- verification-before-manifest.json：建立最終manifest前的檔案／JSON／log核對，不是另一輪測試。最終verify.py只讀manifest與保存檔，不呼叫checker、測試或producer，也不寫檔。
- preservation-after.json：原tracked差異／index、原來源指紋與Git blob的保全證據。檔案一致性不等資料／策略驗收。
- 未保存完整actual：未知來源時間、格式錯誤、月精度、不變性及輸入拒絕等方法內變體；只有原碼與實跑log。未提供私人原件、真實權利、真實精確可得時間；不以合成通過推定已取得。
