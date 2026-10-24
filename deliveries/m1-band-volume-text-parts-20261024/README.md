# 完整band-volume.json：無損UTF-8文字分片

本輪只處理Work工具讀取大檔的交付缺口，不是已證產品計算缺陷。原檔、原ZIP、全部舊成品／五JSON／P0-3狀態事件ID及來源0.10 parent不改；沒有新產品版本、來源0.11或catalog。

Work已回報實看原10張PNG、五項用途差異清楚，並解析五JSON、band-volume-selection及建置驗證內10/16完整快照；**不把這些當完整band-volume.json已讀**。本次不重抓圖、不重跑32 Python／88 Chromium或其他舊驗證、數值producer／指標。

## 分片及重組

- 原檔固定提交：`ec51f617bf51b1ae77099efc4ecd8099d940996d`
- 原路徑：`deliveries/m1-explicit-band-volume-20261024/artifacts/band-volume.json`
- 原大小：**4,102,710 bytes**
- 原SHA256：`03961ba8e322a4a1d2cfde52eeb4840f39b4540b2ad61fec8e55c27328621384`
- [MANIFEST.json](MANIFEST.json)：16片順序、相對路徑、長度、SHA與原檔byte區間。分片路徑相對本目錄；全部讀同一固定交付提交，不混branch head。
- 每片最大262,144 bytes（256 KiB），低於512 KiB上限；各片皆可嚴格UTF-8解碼，切點不在UTF-8字元中間。
- 各片是**文字片段，不是獨立JSON**。依manifest.order取得原始bytes直接相接，**不插分隔、換行、BOM、標頭，不trim、不正規化Unicode或行尾，不重新序列化JSON**。若工具只回文字，須逐字UTF-8編碼後核長度／SHA，不從截斷預覽或Markdown顯示複製。
- 全部串接後先核4,102,710 bytes與上述SHA，再解析完整JSON；不能只讀manifest、10/16快照或部分分片就稱完整已讀。

|順序|UTF-8文字片段|bytes|SHA256|
|---|---|---:|---|
|1|[band-volume.part-0001-of-0016.txt](parts/band-volume.part-0001-of-0016.txt)|262144|`1fb0db347ffd990e5116f2aaf04daf2695034e113b61900bd8a05904ab7ed237`|
|2|[band-volume.part-0002-of-0016.txt](parts/band-volume.part-0002-of-0016.txt)|262144|`f9546ed2fb22e1136cf27529ceb6ea201cd0c1879b225ebef9f0a924433630cb`|
|3|[band-volume.part-0003-of-0016.txt](parts/band-volume.part-0003-of-0016.txt)|262144|`b25aadf74ec9c6f8582cfed1c188275b348772e379644b3fac09fb1fb0b1277c`|
|4|[band-volume.part-0004-of-0016.txt](parts/band-volume.part-0004-of-0016.txt)|262144|`a2857f36fb0466105bbc2b77ee94e48d6fe64dd820e9b6a05d37d69586b23e6a`|
|5|[band-volume.part-0005-of-0016.txt](parts/band-volume.part-0005-of-0016.txt)|262144|`f47b22d8858a36e1e835d741845382003540751fd24440ba56397db6a78277be`|
|6|[band-volume.part-0006-of-0016.txt](parts/band-volume.part-0006-of-0016.txt)|262144|`e6bdff79c0090f914df7c6a9dce5d9d22597636e68c644c7ca6dec8674ceb69e`|
|7|[band-volume.part-0007-of-0016.txt](parts/band-volume.part-0007-of-0016.txt)|262144|`1fc0fa3c110260f7cf819e7170d39924b0cab5a921daaf59e29866446012fca2`|
|8|[band-volume.part-0008-of-0016.txt](parts/band-volume.part-0008-of-0016.txt)|262144|`433965ec63038fc7fd43060a1760dc8fa712b96fd1911fb77772dc592271d4a2`|
|9|[band-volume.part-0009-of-0016.txt](parts/band-volume.part-0009-of-0016.txt)|262144|`20d7aefe840657df8d6b4768f0a9b29ac3378fcd4608620b9e5def553126f37a`|
|10|[band-volume.part-0010-of-0016.txt](parts/band-volume.part-0010-of-0016.txt)|262144|`7dd1b2eee8f78e6d1fc36218c7a5633a3bd5bc713ceee21e31dca34c26376027`|
|11|[band-volume.part-0011-of-0016.txt](parts/band-volume.part-0011-of-0016.txt)|262144|`572904e6a1e0a8afa726fadd35c89a5899cf9270316b3a4610dcb8c84d603620`|
|12|[band-volume.part-0012-of-0016.txt](parts/band-volume.part-0012-of-0016.txt)|262144|`c2be4ead47d7d00b4fcc4b6becc0f3a0155d0684ad8ea88dbeb488b2eab68e62`|
|13|[band-volume.part-0013-of-0016.txt](parts/band-volume.part-0013-of-0016.txt)|262144|`ffb7cbe29d7964b26f039bcfa9a6c007f3e85729a0a2a2289058640e4b8b3a74`|
|14|[band-volume.part-0014-of-0016.txt](parts/band-volume.part-0014-of-0016.txt)|262144|`d9572cdf41f3335511a5d371e158c1b0da720d155e2f636ad11b56e4c9c2823d`|
|15|[band-volume.part-0015-of-0016.txt](parts/band-volume.part-0015-of-0016.txt)|262144|`6a0b7ce1e892bce6a95601e144a01f3f8a7d5688cc8623af1b7ccdab289b0f62`|
|16|[band-volume.part-0016-of-0016.txt](parts/band-volume.part-0016-of-0016.txt)|170550|`a4cd391728dc40b17eb87ab7fe498add481981ac6d4c671a670b61b79416ed0d`|

## 實際封裝核驗與讀回

[packaging-verification.json](packaging-verification.json)：各片UTF-8有效／不超上限／原byte範圍連續；從已寫分片讀回串接後，完整bytes／長度／SHA與原檔相同；JSON可解析且完整物件與原檔相同。不是重新生成／排序／排版原JSON，沒有增減換行。[原檔與固定Git blob核對](source-observation.json)、[原檔全部保持](preservation.json)。[split_utf8.py](split_utf8.py)僅標準庫無損切片／核驗，可供工程稽核，不要求使用者開終端。

[固定GitHub逐檔原bytes回讀收據](GITHUB_READBACK.md)／[JSON](GITHUB_READBACK.json)在交付後另行保存，避免自指SHA。Codex可實際以GitHub raw讀回小分片；目前沒有可呼叫的Work專用GitHub connector，**不冒稱Work工具已取全或完整物件已核讀**，由下一輪Work實際取得後結清。原大檔／blob失敗入口不重試，不用舊ZIP或圖片代替本次交付。

## 下一步只Work

依[WORK_HANDOFF.md](WORK_HANDOFF.md)全文指令：沿用已看10圖，不重抓或重驗；取得同一固定提交16片，核各片後無損串接／解析完整原JSON，完成實際全物件核讀並結清Work本次未取得／未讀項。讀取仍受阻就列具體片號／路徑／錯誤及未讀範圍，不冒已取得，也不要求手機搬檔、終端或架伺服器。

原全部來源／個人權利缺口、B88研究資格與formal_price_bounds=null、Raw／UNKNOWN、策略／引擎／庫／歷史／main及警告保持；不新增密集量峰或選主壓力規則。execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。Android NOT_TESTED_NEW_BUILD、file://不重試。所有受拒入口、library及嘉新逾時路徑不重試或繞過，不重抓來源、ZIP或圖，不公開私人原件、不補零／行情／前價／估值，不跑每日淨帳／六方案或稱已驗獲利。不部署、付費、交易、訊息或子代理。
