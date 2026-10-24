# 2026-10-22 中斷接續核對

GitHub 起點：`cf10dbdb8e8e3e6f59609dfe048e1daa7f5fc1c4`，指定分支 `dev/m1-v018-chart-annotations`；比較最低已知 `e8b7c1f411edf7fc427d9edc70a1c8af94a3fd80` 為 ahead 2、behind 0。

中斷發生在完整視覺研究成果的 GitHub 最終提交前；已恢復原工作目錄，未重建舊研究。51 份待出版檔案清單的 Git SHA 均與本地交付檔相同；建立 tree 時確認八月截止 PNG、完整 HTML 及後續部分檔案尚未上傳，已從原檔補傳並逐份核對相同 SHA。根 AGENTS、CONTINUE、GRAPH_CORE_RESUME_HANDOFF 的遠端全文均完整保留為本地新節之後的後綴，未覆蓋其後歷史。最終以當前 GitHub tree 為基底追加，更新 ref 使用預期父 SHA 保護。

本次實際重驗：
- 18 項 rotation_research.test_core 全通過。
- verify_study 的 9982 項來源／帳務／前綴檢查全通過，70 組同期比較、420 方案。
- 新臨時儲存目錄 CLI RUN/READ 129122 bytes 逐位元一致；sha256 `bcbb54036c4a36ed093e54373d68ce3c5fe317cc71684e6c946bd3a4b6ed3641`。
- 完整 ZIP 4289465 bytes、61 members、CRC 通過，sha256 `38689c8011753092e1fca6698d6c8070906a699621c612a63a2c77872550009a`；封包含完整結果、SVG、截圖與來源清單。
- 重新實看手機頂部截圖及八月雙股 K／量圖；先前 Chrome151 的36項驗收與 JSON/SVG 真下載紀錄已核讀，這次未重跑瀏覽器。Android 新頁實機仍未測。

bootstrap 沿用同一恢復目錄已保存的成功紀錄，不無故重跑歷史驗收。研究採 RAW 的條件式價格報酬扣模擬成本；完整公司行動／股利、歷史可得與日曆仍未核，正式總淨報酬與配置策略未驗證。未修改原數值引擎、舊資料／頁面、正式策略或 main，未下單。

出版提交與遠端讀回收據見後續 GITHUB_READBACK.md；其記錄成品提交 SHA，該收據自身版本以分支最新查詢為準。
