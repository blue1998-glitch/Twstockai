# M-OCI-READ1｜無密鑰工件已備妥，OCI身分隔離受阻

**PARTIAL／BLOCKED_CREDENTIAL_ISOLATION。不是Oracle已連線，也不是官方API已拒絕。**

已核總監實際驗收：request6650802405 → native run41976315386 completed/success → bot6650805038 PING_OK，固定私庫6015e6b834fcd24cf13f0b43648d76fa4c443cac，source/workflow pins相符。GPT_TO_GITHUB_RUNNER_CONNECTED僅限PING，原生成功原回應已讀並留Git外，安全投影見[CTRL1_ACCEPTANCE.json](CTRL1_ACCEPTANCE.json)。沒有重發PING／重跑舊驗收。

## 已交工件

[Twstockai_OCI_READ1_KEYLESS_STAGE.pyz](Twstockai_OCI_READ1_KEYLESS_STAGE.pyz)，6796 bytes；SHA256 `bea042bf81b7d9563976ee30af1469f7de28caafcdc6734d99045254705cdd60`。純stdlib離線inspect／check-command，驗完整manifest／CRC／成員／原bytes，無網路、無execute／apply／force／啟用參數。包內原OCI SDK adapter與sanitize保持原bytes（SHA256 `85901ba5da028523df8bff8bac60984a103afa33e6c2a1e8de5126adb8948507`）；沒有重新實作金融／SDK引擎、安裝依賴或產生憑證。

新增protocol.py只接受兩欄固定命令，提供脫敏結果投影，不是身分驗證器。投影明示NOT_ATTESTED_BY_PROJECTION，不能當真實Oracle收據。完整native READ1授權／nonce與Oracle身分整合**未實作、未啟用**；沒有把舊receiver的installation必填邏輯或PING-only信任直接升格為OCI授權。

原Codex可直接用 `python3 codex/oci_read1/Twstockai_OCI_READ1_KEYLESS_STAGE.pyz inspect` 核工件狀態；不用使用者操作終端。此入口不執行Oracle、不接收secret、不建立資源。構建入口 `python3 -m codex.oci_read1.build <隔離輸出路徑>`，不得拿本工件冒充可發OCI指令的部署包。

## 精確停止點

Oracle JWT→RPST官方頁已實際讀取：第三方JWT仍需IAM Domain OAuth client（官方示例Basic clientid:clientsecret），或OCI Service／Instance Principal簽署交換請求。GitHub id-token:write只允許取得GitHub JWT，不能提供Oracle呼叫者身分。最多5條claim validations、最多3條claim propagations亦有官方限制；真實Oracle trust／JWT claims／client／pilot／帳戶費用均未取得，不生成猜測可啟用配置。

若之後核准federation，必須驗簽／issuer／aud／exp／nbf／iat、固定repo_id／private／workflow ref與SHA／event，owner與App再由canonical REST核實；不能拿文件中的claim名稱當已核實本帳戶token，更不能用performed_via_github_app當installation證明。當前PING workflow仍沒有id-token:write，未修改它。

原環境沒有OCI secret／runtime identity，也沒有已批准的新密鑰保存位置。現有Free private Environment Secrets路線已停止，未改用Repository Secrets、OAuth client secret或API key。不得把未知身分改成OCI官方403，也不能以Free Tier陳述證明IAM federation／主機可用／全配置零費用。

**唯一方案與本人集中動作**：[OWNER_SECURITY_BATCH.md](OWNER_SECURITY_BATCH.md)。優先既存合格免費隔離主機＋Instance Principal＋一次性runner，無長期OCI key，但主機實況未知，且Instance Principal固有compartment_inspect／self-hosted風險須本人明示接受。無既有合格主機就停止，不新建，不以臨時試用抵扣。這是待批准方案，不是本輪部署成果。

## 實際驗證與尚未完成

4唯一新方法只測純命令、未知結果保持null／投影非attestation、封包重建原bytes與離線無啟用入口；沒有SDK／Oracle／身分交換mock。舊PING／既有工程套件全部未重跑。封包CRC／manifest與重建一致；[verification.json](verification.json)、[tests-stage.log](tests-stage.log)。

真實Oracle API呼叫0、OAuth／RPST交換0、取得JWT0、載入Secret0、新建Oracle資源0、新workflow0；READ1真實成功與官方拒絕皆未取得。現有pilot／AD／專用身分／IAM／主機免費資格未知。精確官方錯誤留證與新READ1native auth／nonce／一次性runner整合尚未實作；舊adapter將API例外投影UNKNOWN，不能稱其已有可驗官方拒絕收據。

原私庫四個CTRL1部署檔保持；本輪只存inactive read1/工件，不啟工作流、不發指令或bot收據、不更改US$0預算。原Cloud、FM3／owner／512MiB／880歷史未追蹤、來源／策略／main保持；不搬資料／建機／付費／交易。

交總監核身分與隔離方案後停止。本輪不把工具校驗冒充Oracle實讀；只有後續授權、真實API及ChatGPT讀回都完成才能標OCI_READ_CONNECTED。
