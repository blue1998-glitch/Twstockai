# M-ORACLE-SHELL1｜Cloud Shell安全查核工具（部分交付）

**可執行的inspect／plan／status／stop及apply拒絕閘門已完成；成功建機與私人HTTPS後段未實作。不是完整自動部署工具。**

固定工具包與可貼指令見[交付入口](../../../deliveries/m1-oracle-shell1-20261104/README.md)。只需使用本人已登入的Oracle Cloud Shell；不填OCID、不貼密碼、OTP或私鑰。Codex沒有真實Oracle登入，不能聲稱帳戶已查核。

## 可做什麼

- 單一stdlib Python zipapp，使用Cloud Shell既有官方OCI CLI與原登入設定，無pip／新帳戶／外部服務。
- inspect：以精確list/get白名單查租戶、Home Region、已發現compartment及AD、Compute、Boot／Block、VCN／subnet／各scope公網IP、映像、Shape billing-type、limits與resource-availability。每項權限、頁碼、時間／數量／大小限制保留；看不到不填0。
- plan：十分鐘有效、綁工具bytes／原檢查指紋／帳戶／區域／固定合成包的HMAC私有計畫。未證條件列UNKNOWN，resources_to_create為空，只有阻塞提案。
- apply：驗MAC／版本／期限與帳戶，再重新唯讀核對實際條件；不足即拒絕。**本版沒有Create／Update／Delete或成功部署後段；即使自行改旗標也不會建機。不能宣稱已完成成功部署重送驗證。**
- status只讀上次私有快照，明示不是即時資格；stop明示本工具尚未建服務，沒有擅自停止他人主機或刪資源。

完整私有觀察／計畫／HMAC key只留本人Cloud Shell的`~/.local/share/twstockai-oracle-shell1`，目錄0700、檔案0600、排他鎖與容量上限。公開輸出僅中文狀態及計數，不回顯OCID、AD識別、IP、CLI原stderr、登入token或密碼。不可將私有JSON上傳GitHub或貼聊天。

## 為何仍停止，不能假裝已能建機

本次確實查閱官方Shape模型，存在billing_type=ALWAYS_FREE／LIMITED_FREE／PAID；只接受ALWAYS_FREE原值作**Compute分項**證據。LIMITED_FREE、服務配額、餘額、可列機型或Oracle Linux名稱不代整套免費證明。

BootVolume／Image／Vcn模型沒有同等完整billing-type欄位；本版**尚未完成**整套帳戶／儲存／IP／映像／網路零計費證據讀取器，不能宣稱所有Oracle API永遠無法證明。實際容量文件使用`compute-capacity-report create`，inspect／plan依授權禁止此操作；機型清單不當實際供應。Personal免費方案、本人同意及最小ACL也尚未取得。這些項目維持UNKNOWN，沒有人工--force、手改plan或模擬證據的放行入口。

已取得官方公開文件的URL／SHA見[docs-acquisition](docs-acquisition.json)、[component-docs](component-docs.json)，原bytes在原Cloud本輪Git外目錄。Work的兩個控制台Site Unavailable只沿交接，不重試；本人Cloud Shell為新的正式備援路徑，不再派Work重做登入研究。

## 工程驗收與界線

20唯一新mock／封包／隱私／計畫測試PASS；初次測試檔案路徑寫錯造成測試模組匯入失敗，當時領域方法0，已保存並修正，不將loader的1算領域測試。不累加中間批、不重跑原16合成產品／15瀏覽器。

覆蓋唯讀白名單、禁止任意OCI參數、錯Home／權限／配額／來源SHA拒用、計畫過期／竄改／帳戶或版本錯配、重送拒絕零建立、ZIP路徑／唯一名／symlink／CRC／manifest／完整來源指紋、私有權限／鎖與安全摘要。**沒有成功建機／部署後斷點恢復／部署後冪等的工程或真實驗收**；沒有用拒絕路徑代替成功部署驗證。

固定原pilot ZIP仍345616B／SHA256 `0c48c1d92a94cfcfc1a88f52c22c97cda0d9f0797a05d0367a32ca1fc4a6e750`，原26成員完整核對，不改bytes、不重建UI。原Cloud／FM3／owner8765／view-head、來源0.10／parents、策略與main不動。未搬行情、部署、付費、啟排程、交易、VPN或代理。

最終固定下載指令與實際GitHub下載／校驗／啟動檢查將在交付README及bootstrap驗證中固定；在原Cloud隔離HOME驗到缺登入安全停止，不當真正Cloud Shell帳戶驗收。成功建機功能仍屬**未完成**，不是只差使用者按apply。下一步先用本人Cloud Shell跑唯讀入口取得安全摘要，不提供憑證或完整私有清單。
