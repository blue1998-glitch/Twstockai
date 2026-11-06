# M-PROD-DAY4｜11/5 正式全市場單日批次已發布

Issue #8完成。原同一owner **http://127.0.0.1:8765/** 已預設11/5；這是Cloud本機位址，Android外部仍未連，不是手機網址。搜尋1986檔、查看當日OHLCV、逐股核心狀態及保存結果按需圖；日期頁保留11/3、11/2、10/30與舊多股比較，沒有另建預覽或第二網站。

上市1089：1085核心完成、4來源拒用；上櫃897：882完成、15拒用。新核心1967、Journal1986、工程失敗0。每股只有一根經認證可比K，**1967均歷史不足**，MA／MACD暖機null、無完整多日結構，不造突破、回測、失效或交易建議。拒用7缺報價、7無有效收盤／停牌未認證、4零量、1品質失敗，原值與拒用理由保留。

## 真實接件與保存

原canonical上櫃完整HTTP200 body逐bytes核實後重用（5,329,099 bytes；SHA見source-verification），沒有新的上櫃行情GET、不拼舊partial。其餘五來源各一次HTTP200完整，重試0、轉址0。原market_increment.sources核六件同日、官方URL、CFI／ISIN／普通股與股數單位；1986是本次來源參照，歷史母體涵蓋仍UNKNOWN，不藉此升格。所有完整HTTP／安全headers／起訖／原bytes／fact／Journal留Git外 `/workspace/twstockai-local-data/prod_day4_20261106`；Git僅程式、合成測例與不可還原摘要。

最初容量預檢證原pretty Journal方式超出安全餘量。新批使用明示MINIFIED_UTF8_V1 wire（完整同物件／精度／null／schema），原Journal.reader直接讀；大型新manifest／index／HTML／action繼續用既有DU2 exact-byte codec，所有descriptor仍綁還原原bytes及SHA。原Journal與scan1 source、原金融核心／parser／MA／MACD不改，舊批永不重編。scan_io只是原scan1流程的I/O適配：同fact／validate／key／worker／checkpoint；沒有第二數值引擎。source_reader重用原保存結果／RAM cache與白名單，cache HIT前仍驗來源DU2依存、原fact及版本。

新操作budget使用本輪immutable baseline，不改舊baseline；資料寫入逐筆512MiB guard維持；第一次Git索引暫存低點未量測、可能低於保留，不能宣稱全程最低已核。第一次提交後free537202688仍高於保留；收據保存改以/tmp暫存Git索引（僅可重建版本控制metadata，市場資料仍在持久磁碟）。新單筆Journal≤4096 bytes、scan600秒、原worker256MiB AS／3秒CPU／8秒wall、CLI512MiB AS。未刪除／搬移／覆寫任何行情原件，未使用tmpfs作持久資料；瀏覽器臨時profile依原工具位於/tmp，驗收紀錄保存原私人磁碟。

## 原環境單次維運入口

由唯一Codex先即時核Cloud與原engineering.lock，再以既有`codex/unified_workspace.py --environment-id 本輪工具實核ID --run`持有lease，設定原PYTHONPATH後執行：

```text
python3 -m graph_core.prod_day4_20261106.run
```

本入口只對已明示11/5來源stage負責，不接受換日繞過。已有source receipt則驗bytes、GET0；有新manifest則重核其pins，續行原逐股checkpoint；全部完成才能prepared→同owner驗證就緒→product head。重送新程序實測0 GET／0核心／0新record／0檔案修改，3.50秒。只讀狀態沿原`graph_core.prod_core1_20261105.flow status`。未啟排程、不要求本人開終端。

## 本輪驗收與限制

[summary.json](summary.json)、[source-verification.json](source-verification.json)、[verification.json](verification.json)、[resources.json](resources.json)、[tests.log](tests.log)可直接讀。7唯一新Python（初6、終7不相加），19新日期瀏覽器流程群（390直向、844橫向、1280桌面）及6權限控制；兩市場各2真實案例逐欄核對，全1986 source→fact及Journal都由重送重新驗讀，不重跑舊1955核心／舊26瀏覽器套件。舊11/3原保存圖、11/2與10/30圖／比較仍可開。

真實全批87.57秒，含來源再核與view90.71秒；協調器峰337672KiB、worker119920KiB；新首頁1,956,824 bytes，手機尺寸首次881／810ms，JS heap約4.6MB，僅本機工程量測。新stage實體19,783,680 bytes、FS淨增20,869,120 bytes（驗收時；最終Git文件會小幅再增），free537,772,032 bytes，仍≥536,870,912。新Journal實寫8,134,656 bytes；同實際物件若pretty wire計算16,191,488 bytes，此對照是計算，不聲稱另寫一份。新批不複製FM3歷史或預製全市場大圖。

目前有真實新日與全市場執行，不等合格多日／Android本人實機／正式交易／每日自動化。獨立備份與重啟持久性仍UNKNOWN；Cloud未重啟，只受控重載同一owner並保留原設定。FM3 PORT1的90377 metadata沿用核實、原來源heads及880歷史未追蹤保持；全部來源0.10及parents、策略與UNKNOWN／false/null不變。

[Issue #7願景](https://github.com/blue1998-glitch/Twstockai/issues/7)僅作未來五層決策大腦／全帳成本後成長的方向，未在本輪新增策略。主動全面持現金、重新進場與機會成本仍待研究及正式批准。完成固定工程逐檔GitHub原bytes讀回後停止；總監可決定下一輪手機私人入口、排程或多日資格，本輪不擅自啟動。
