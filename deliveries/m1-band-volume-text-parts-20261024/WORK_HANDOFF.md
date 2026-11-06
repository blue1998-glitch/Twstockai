# Work唯讀：取得分片並核讀完整band-volume.json

使用Codex本次回覆的固定交付SHA與最新已核SHA；固定讀回另見同目錄GITHUB_READBACK.md／JSON，收據不自指。

```text
接續blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations。
先唯讀核包含本次固定文字分片交付、最新讀回提交、bd6ed6a984254295eae4c13c5973ef28a7b7c29b及原固定工程ec51f617bf51b1ae77099efc4ecd8099d940996d，保留全部後續，不回退、強推或用main／舊ZIP覆蓋。

本輪只Work唯讀取得與解析已保存JSON，不bootstrap、工程、產品測試、數值producer、指標、commit／push；原既有唯一Codex仍是唯一工程寫入者，不另開Codex、平行工作或子代理。

優先讀deliveries/m1-band-volume-text-parts-20261024/README.md、MANIFEST.json、packaging-verification.json、source-observation.json、preservation.json、GITHUB_READBACK.md／JSON及本交接全文。根最新交接、M1_EXPLICIT_BAND_VOLUME_HANDOFF.md及全部parent的來源／策略限制保持；舊交接要求看圖或重驗的部分，以本次「已看10圖、只補完整JSON讀取」為準，不重做。

已實看原10張PNG且五項用途差異清楚；原五JSON、band-volume-selection、volume-build-verification內10/16完整快照已解析，沿用既有證據。不能把這些、Codex封裝驗證或manifest當作Work完整band-volume.json已取得／已讀。

只從本次固定交付提交取得MANIFEST所列16片UTF-8 .txt，每片不超256 KiB；各片路徑相對deliveries/m1-band-volume-text-parts-20261024。使用唯讀GitHub工具取得完整原始內容，不混不同提交、不用截斷預覽，不重試原大檔／原blob失敗入口，也不重抓原ZIP或圖。

逐片依manifest.order核bytes及SHA256，按原bytes直接串接，不能插入／刪除換行、空格、BOM或分隔，不能trim、Unicode／行尾正規化、排序或重排JSON。分片本身不是完整JSON；工具只回文字時，原樣UTF-8編碼後核長度／SHA，證據不符就停止並列實際錯誤，不造匹配結果。

原完整JSON必須是4,102,710 bytes，SHA256：
03961ba8e322a4a1d2cfde52eeb4840f39b4540b2ad61fec8e55c27328621384
對應原固定ec51f617bf51b1ae77099efc4ecd8099d940996d：
deliveries/m1-explicit-band-volume-20261024/artifacts/band-volume.json。

核整體長度／SHA後解析完整JSON；分清「bytes已取得」「串接指紋正確」「JSON已完整解析」「實際核讀範圍」。只讀已保存完整物件，可列根鍵與snapshots數量作取得範圍說明，不再逐日驗算比較、重跑語義／核心／來源配對驗證或既有驗收；不跑producer／32 Python／88 Chromium，不用10/16單快照替代完整檔。若工具不能取得某片或無法完成串接解析，列片號、固定路徑、實際錯誤及剩餘未讀範圍，不聲稱已結清，不要求使用者手機下載上傳、開終端或架伺服器。

本次只補交付讀取缺口，未發現已證產品計算缺陷，不新增產品版本、來源0.11或catalog。原五JSON、P0-3狀態／事件／ID、角色及26.95／26.85／20.25價格參照、策略／原引擎／庫、Raw null／UNKNOWN、歷史／舊成品／main及全部警告保持。B88仍RESEARCH_CANDIDATE、formal_price_bounds=null；密集量峰代表線未實作，不自行新增箱界、量倍數、比例、天數或主要壓力規則。

全部parent及來源／個人權利缺口保持。年報／CTBC／公開說明書／舊ZIP／圖不重抓；全部受拒入口、library及嘉新逾時路徑不重試／換主機路徑繞過。私人原件不公開，不補零、行情、前價或估值。
execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。
Android NOT_TESTED_NEW_BUILD，file://不重試，不跑每日淨帳／六方案或稱已驗獲利。

最後分列已完成與未取得／未讀／未實作／未執行／未測／未讀回；只有實際取得串接並完成全JSON核讀後才結清本次Work未取得／未讀項。沿用已看10圖不重抓，不以本次封裝冒新產品或策略驗收；只選一個下一執行對象並附完整指令。不部署、付費、交易、發訊息或啟動子代理。
```
