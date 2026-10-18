# M1 人工價量時間區域主圖 0.3

新增獨立主圖接入G1／G2人工時間帶、原代表點、C開放參照、拖曳查詢、逐交易日OHLCV及獨立未提交草稿。保留舊版與歷史。G2已確定2023-01-16～2023-08-16；G1精確九月起日與價格／量度規則仍未定。這是已明確UI工程完成，核心用途仍NOT_ESTABLISHED，Android NOT_TESTED_NEW_BUILD。

## 下載與操作

- [下載小ZIP：4.37 MB](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/31d80971b265942eb3d7573fddf00f6782f20a55/deliveries/m1-v019-manual-regions-v03-20261018/M1_v019_manual_regions_v03.zip)
- [ZIP SHA256](SHA256SUMS.txt)、[ZIP實際解壓／CRC及各檔SHA](PACKAGE_VERIFICATION.json)
- [HTML原檔（36.74 MB，請下載後開啟）](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/31d80971b265942eb3d7573fddf00f6782f20a55/%E8%82%A1%E7%A5%A8%E7%B3%BB%E7%B5%B1M1_v0_18/region_chart/generated/M1_v0_19_manual_regions_v03.html)
- [完整可直接貼Work指令](WORK_HANDOFF.md)
- [本輪實測報告／實際畫面／失敗及未測](../../股票系統M1_v0_18/region_chart/validation_20261018/驗收報告.md)、[來源檔指紋](SOURCE_HASHES.json)
- [GitHub實際下載核對收據](GITHUB_DOWNLOAD_VERIFICATION.json)：已實際PASS，固定成品提交129檔共55,089,638 bytes逐字核對，下載ZIP CRC／解壓SHA再核。此後README／Work指令／收據另作交接提交，不宣稱其自我包含於舊成品收據。

解壓後開`M1_v0_19_manual_regions_v03.html`，標頭「M1 價量區域主圖0.3」。1101／Raw｜新官方日線／2026-10-16，日收27.30、24月486根。按G1／G2／C後聚焦，區域證據看來源；24月返回近期視窗。預設拖曳查詢只移游標，明選移圖才平移，可雙指／＋−縮放。主圖下方選交易日、前後一筆讀完整OHLCV，分析日不變。「選點草稿」可記起終點、複製或下載獨立草稿；重開／換來源或分析日清空，不提交／批准。

ZIP SHA256：`ef258e1dfa1bd965168f630c642b56475cc132fc7184b85dbbfe999e1fde2f9b`。
HTML SHA256：`0a1513b361c1473c4e38bb3c5db2f3477054fe2bb4779592f31b5b73fc84bb8e`。

原0.1／0.2及Android證據原樣保留：[0.2入口](../m1-v019-hurdle-labels-v02-20261018/README.md)。舊0.2手機PARTIAL_EVIDENCE_OBSERVED，不重索同版相同圖／JSON；0.3另記NOT_TESTED_NEW_BUILD，只驗新增差異。已知file://管理政策阻礙未重試／未繞過，手機若受阻記具體錯誤，不停用保護。HTTP模擬與數值檢查不等於Android或核心用途認可。

## 本輪實際結果與限制

16項區域Python及完整383項Python通過；最終HTML真實Chromium208項HTTP、44標籤、55區域檢查通過（四尺寸、原生滑鼠／CDP觸控、100全精度下載、專項草稿下載）。整體runner保留PASS_WITH_KNOWN_BLOCKER，舊file政策阻擋未重試。244來源檔、4854新Raw與1490原frame、50oracle、凍結parent、案例指紋及ZIP CRC核對通過。舊1316追蹤檔無未預期差異，只有4份交接增最新狀態；來源／庫／舊成品／證據不變。不是歷史118／10／208／44代填，新版各runner實際重測，失敗記錄保留。

G1起日、區界、整區量及量口徑、增量、強度／衰減、自動分區／選關、生命階段未定，不發明正式規則。C後定性判讀不認證持股。Raw完整公司行動／五年Adjusted／歷史公布可得與原來源缺口、SQLite未知根因保留；五年高不是全史高、日OHLCV不是精確分價。Darvas正文未完整讀、無箱型規則採入。無部署、付費、交易、訊息、子代理或main改動。

完整source在指定分支；此小ZIP僅自足頁面及原案例，不冒充完整專案備份。下一步用**Work**，貼[WORK_HANDOFF.md](WORK_HANDOFF.md)全文驗本版差異；可重現工程錯誤再回Codex。

成品提交：`31d80971b265942eb3d7573fddf00f6782f20a55`，已推送並實際由GitHub下載。最新交接另沿同一分支；遠端main仍`9c5b168c09ba80010c74f03b9c537e8b7474256a`。下載入口固定此成品提交，不隨後續分支修改而漂移。
