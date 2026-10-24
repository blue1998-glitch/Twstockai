# 橋接ZIP固定提交逐檔GitHub回讀

固定附件提交：`8aecb50bfcae0401ea77234a755cebe6b5277d63`，parent：`a52cff207066b1180b6a4e656cf7b49e8ffe4cc6`。
觀察時間（UTC）：2026-10-23T06:42:48.628Z。

本輪實際透過GitHub從固定提交讀回ZIP原始base64、README及.sha256三檔，均與本地完整內容逐字節等價。ZIP為941229 bytes，SHA256 `ecc413ca28fce87085666b87b3c3a6d1bf784ef553b32d2198b8bb72bebeedce`；遠端完整base64與已核本地原包一致，非只核檔名／摘要。ZIP CRC及40個manifest列項長度／SHA已核，共41成員。各blob SHA與比較見GITHUB_READBACK.json。

這次依使用者新增授權只交付附件與證據；沒有bootstrap、產品工程、新產品測試或來源新版本。舊61項不是本輪重跑，Codex是否實際取得本包仍未驗證。所有既有資料／成果／策略／引擎／庫／Raw null／UNKNOWN與main保持，沒有重試被拒來源或子代理。

既有唯一Codex可直接從本分支本目錄ZIP取得原件，核完整封包及成員後，讀包內完整CODEX_HANDOFF.md，重新bootstrap成功才實作。原研究包內GitHub頭與0寫入等數值為封存歷史，沒有改動原包。收據另正常提交以避免自指SHA。
