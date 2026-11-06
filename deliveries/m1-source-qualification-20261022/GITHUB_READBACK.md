# 官方來源資格補充：固定交付與GitHub回讀

儲存庫blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations。

- 使用者已核起點：50d8c5e36285a2c3cd107a9a7a0dd7596c22b2ea。
- **固定完整成品提交：c7362fe27435659a7d8624e0f4ae8c109333f7a1**，以50d8c5e為父，提交前核對遠端預期父提交、正常非強制推送。
- 與起點相比全部87個本輪變更檔案，均從固定成品SHA的raw.githubusercontent.com URL實際讀取，HTTP200且逐位元等於本地，無失敗；每檔URL／長度／SHA256／核對時間在GITHUB_READBACK.json。官方原件保留原有空白，沒有正規化或重寫。
- 其中新ZIP 671142 bytes／375 members，GitHub讀回SHA256為2411f934b290edd3f65cb30b5ebb3b20c9aba9fb5099e454fd5a57e335652542。CRC／374 manifest成員SHA全通過，原事件帳293成員bytes完整保留；新目錄解壓15來源測試與producer成功，重現後374成員仍全等，CSV473行／317市場日／兩個null也核對通過。
- remote branch ref在全檔回讀前後皆為c7362fe27435659a7d8624e0f4ae8c109333f7a1；main仍9c5b168c09ba80010c74f03b9c537e8b7474256a。

[固定小ZIP](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/c7362fe27435659a7d8624e0f4ae8c109333f7a1/deliveries/m1-source-qualification-20261022/m1-source-qualification-v01-20261022.zip) · [固定來源報告](https://github.com/blue1998-glitch/Twstockai/blob/c7362fe27435659a7d8624e0f4ae8c109333f7a1/股票系統M1_v0_18/rotation_research/source_qualification_20261022/REPORT.md) · [固定完整Work接續指令](https://github.com/blue1998-glitch/Twstockai/blob/c7362fe27435659a7d8624e0f4ae8c109333f7a1/股票系統M1_v0_18/rotation_research/source_qualification_20261022/WORK_HANDOFF.md)

本收據在成品之後另存，收據自身最新SHA請查分支ref，不與固定成品混淆、不假造自指指紋。起點3030原追蹤檔中3024檔bytes不變、6交接只加前綴且舊原文後綴完整、無刪除；原ledger／策略／庫／價格／舊結果及所有舊ZIP保持，見source_qualification_20261022/preservation-audit.json。

本輪不是全部資料資格完成：只補核指定TWSE窗口的317市場日，70窗口仍因其他行動／淨分配／期初權利拒算，2不足，總淨報酬合格0；15新測試不與前輪44或P1-7舊18／9982／Chrome36相加，舊測試未重跑。沒有新策略成交／勝出比例，沒有UI／瀏覽器／Android。本輪新歷史減資請求HTTP307根因未確定，診斷capture清單無保留記錄，不當空表或已修復；當前預告與申報零命中也不證無事件。

環境設定草稿已保存network.allowed_domains及start_skill，工具requires_publish=true。保存後另核runtime：observations_current=true、spec_revision=2，自訂域仍只有TWSE／TPEx、policy state unknown；兩新域尚未見套用、未實測可讀。www.esunbank.com的舊PDF403未原樣重試；mops.twse.com.tw尚未請求。使用者需在產品環境設定檢閱並按其流程套用草稿，不能由GitHub交付代替此步；未代為發布環境或部署。具體URL與所缺欄位已保存，不需要使用者猜策略比例。

下一步Codex於必要設定生效後核對特定來源，補公司行動／配股比、可交易日、零股／淨分配及期初權利；缺失維持未知或拒算。原禁權息端點及file://不重試不繞過，不改main，不部署付費交易訊息或子代理。完整接續指令在source_qualification_20261022/WORK_HANDOFF.md。
