# 後續最小網路草稿：已保存，未套用／發佈

在固定歸檔dd8eae9980c95629ddefe0e7123b14a7efdb8a65及其15文件逐檔讀回後，原唯一Codex繼續完成可做的環境準備。兩次已受拒來源沒有重試；原歸檔內「未改網路設定」描述的是當時取得嘗試，現在另有本節這份**未套用草稿**，不是已更改runtime或解除限制。

已透過Cloud Environment Onboarding正式工具讀取完整現行草稿，僅替network.allowed_domains保留原十個自訂域並加入 `ecorp.ctbcbank.com`。沒有加入chatgpt.com、萬用域或其他目的地，沒有更改repository／ref、install_script、start_skill、secrets、環境變數或套件presets。保存status=saved、requires_publish=true；再次由後端讀回確認revision11、完整十一個自訂域及所有無關欄位不變，詳network-draft-review.json。

其後只讀runtime狀態仍spec4／observed4，CTBC尚未在runtime allowed_hosts。沒有發佈環境、執行腳本、重啟、修改代理／CA／TLS或做來源GET；不宣稱網路已通或原件已取得。代理CONNECT403以外的拒絕原因仍未知；這個草稿也不保證官方來源一定可讀。

## 下一步由使用者在環境設定完成正式授權

1. 開啟目前附加雲端環境的設定，檢閱自訂允許網域只新增ecorp.ctbcbank.com。
2. 儲存變更並發佈環境。草稿保存與發佈／runtime套用是不同狀態，不必下載或上傳任何檔案。
3. 留在本原既有唯一Codex，貼下方授權文字。沒有明示新授權及可核的設定變化前，不重試已受拒URL。

```text
環境設定已檢閱、儲存並發佈，請由此原既有唯一Codex繼續。
先核遠端最新分支與交接、讀network-draft-review.json並核runtime是否已有ecorp.ctbcbank.com。
若確已套用，我明示授權對以下精確URL重新嘗試一次GET：
https://ecorp.ctbcbank.com/cts/static/ag_dividend_printer.jsp
不跟轉址、不再重試；仍受拒即停，不換主機、路徑、代理或認證。
不要重試chatgpt library或其他舊拒絕入口，不建立另一Codex或子代理。
若取得，保存原始bytes、URL、HTTP、headers、開始／完成時點及SHA；核真實表頭、製表日期、年度與1101／1101B列，作為新Codex捕捉，不冒Work原件或Work完整交接已取得。
先評估保存或工程實益，不為湊版建0.11。遵守本輪完整CTBC界線、0.10契約及所有拒算／未知旗標；必要工程才按AGENTS重新bootstrap、定向實測及相關回歸、正常提交指定分支與固定逐檔原bytes讀回。未取得／未讀／未實作／未執行／未測／未讀回分列，不部署、付費、交易或發訊息。
```

本流程來自 [setup SKILL.md](skill://plugin_connector_1p_ed5feb9070a08191b08c81c47947bc16/setup/SKILL.md) 與設定工具requires_publish=true。技能原文：「Saving persists configuration; it does not execute scripts, apply runtime changes, or publish.」本文件只準備可檢閱設定，不要求下載上傳，也不把使用者未回覆或時間經過當成新授權。

研究包與WORK_RESEARCH_HANDOFF、Work／Codex CTBC原件仍未取得未讀；MANIFEST及四筆參照列未核，沒有產品／回歸測試、producer或績效。全部來源／版本／策略／庫／Raw null／UNKNOWN／歷史／成品及main不改，所有資格旗標維持。完整Work唯讀交接仍見WORK_HANDOFF；下一步實際操作應留在此Codex處理環境套用及新授權，不再要求Work重送同一不可讀網址。
