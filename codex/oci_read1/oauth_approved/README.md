# M-OCI-READ1 OAuth正式批准版｜條件式執行器已實作，帳戶資格待本人核實

**目前NOT_CONNECTED／DEFAULT_DENY_ACCOUNT_UNKNOWN。儲存風險已批准，不再問相同授權；真正Oracle讀取尚未執行。** 最新原件[AUTHORIZATION.json](AUTHORIZATION.json)，Issue #2 comment6651585478。舊self-hosted／Instance Principal方案已被本次OAuth路線取代，不建立主機，不執行舊OWNER_SECURITY_BATCH。

## 已交實際程式

`Twstockai_READ1_OAUTH_RUNNER.pyz`，62311 bytes，SHA256 `82f7c2397104f710950503343abf73a53e6e6b1ade0ae5f8a37ec80e1cfac58c`。可執行authorize／prepare／read，離線inspect只回DEFAULT_DENY；沒有任意shell／URL／OCI ID／region的命令入口。公開只有程式與預設UNKNOWN模板，私庫才有正式workflow／來源App綁定／未來account.json；密鑰絕不進封包。

native.py重用CTRL1的API／嚴格JSON／指紋／時鐘，實作獨立READ1身份：private Issue1、owner／來源App／REST權限、canonical未編輯5分鐘留言、native run／triggering actor／repo／event／attempt／ref／SHA、完整workflow原bytes與package pin。沒有偷用PING-only當OCI授權，也不聲稱installation證明。固定兩欄`oci-read/0.1`＋`list_pilot_compartment_resources`。

兩個job：authorize不含Secret與id-token權限；只有帳戶觀察／版本／持久bot nonce全部成立才允許read job。read先重新驗證並把該run nonce由AUTHORIZED→EXCHANGING，安裝25項完全雜湊鎖定的官方SDK相關依賴，再在唯一credential step提供`OCI_READ1_CLIENT_SECRET`。source/schema、帳戶UNKNOWN／過期、nonce已用或不屬本run皆在取Secret前拒絕。全repo原concurrency不取消執行中job；GitHub只有一個pending的原生限制仍在，不稱無限可靠佇列。

federation.py從平台OIDC URL取短效JWT，以固定GitHub JWKS／RS256驗issuer／audience／時間／sub／repo_id／private／actor／trigger event／workflow/ref/SHA／run id與attempt，才讀專用OAuth Secret。對官方domain `/oauth2/v1/token`發一次Basic client認證的JWT→RPST交換，requested_token_type明定OCI RPST、回應只接受`token`而非`access_token`；TLS驗證開啟、無redirect、不複製文件中的-k。

短效RSA key只在RAM，RPST請求5分鐘、只接受短期限；用官方SecurityTokenSigner與原OCIReadAdapter factory，僅ListInstances／ListBootVolumes／ListVolumes至server固定既存pilot與合格AD，不建另一個清單引擎。NoneRetryStrategy、32請求／每類500資源與16頁、90秒實讀期限。只投影數量／允許狀態與精確HTTP／固定官方錯誤分類、request ID雜湊；不回OCID、IP、帳戶、raw token／response／exception。傳輸／SDK未知不算官方拒絕，list attempts與有HTTP證據的Oracle calls分開，未知維持UNKNOWN。

## 官方資格已核與本人資格未知

[sources.json](sources.json)記錄實際HTTP／SHA。Oracle官方Free表的第三方OAuth欄有Checkmark、Identity Propagation Trust總上限30、Free身分域不使用meters；不是「本人剩30」或本人domain／region已開放WIF。JWT→RPST頁明確為OCI Control Plane resource principal；SDK model也有Resource、publicKeyEndpoint／impersonatingResource／claimValidations等欄位。官方最多5條claim validations，本版trust建議精確repo_id／workflow_ref／workflow_sha／event_name／aud，程式另驗actor/sub/全部native條件。

**本人實際domain type、區域rollout、剩餘配額、既存獨立pilot、精確IAM principal映射／最小List政策、runtime client無管理角色、原生READ1 JWT均UNKNOWN／未取得。** 不能用租戶Free Tier或文件存在升格本帳戶已合格；不產生猜測的any-user IAM政策。當前account.json預填UNKNOWN、啟用variable未由Codex設定。未核資格前不安排client／Secret啟用。

## 本人唯一集中指南

[OWNER_ONCE.md](OWNER_ONCE.md)：先只在既存Oracle查看Free domain、WIF／Region／Quota、獨立pilot與精確IAM。任一未知即停，不輸入Secret、不建資源。全部成立才在同一份指南繼續本人OAuth client／受限trust、單一private account.json、Secret直送GitHub與最後啟用variable；不用本人算hash或終端，不傳敏感截圖／值。既有儲存風險正式批准已預填，不重批。

Repo Secret不能被真正限制到單一workflow。私庫寫入者可改workflow取Secret，此剩餘風險已正式接受；固定SHA／雙job預檢不能冒Environment approval或branch protection。Code review與使用上限／撤銷都在指南，不修改US$0阻擋。原PING四檔保留且不加Secret；真正READ1啟用時本人停原PING workflow避免無關拒絕，不重跑它。

## 這輪實跑與未實跑

17唯一新定向方法通過：原生REST合成授權、實際RSA簽章的合成JWT、期限／schema／source／nonce／run綁定、官方請求格式、錯誤脫敏與未知計數、完整依賴圖、兩job安全分層／bootstrap編譯、封包重建與授權後回覆整合。初次15方法有2個錯誤（拒絕例外型別、YAML scalar），已最小修復，原log與source指紋保留；後續相關重跑不累加為新方法。舊PING／研究／套件／探針均未重跑。

本地PyJWT／cryptography與將來25項鎖定依賴版本分開：**沒有在原Cloud裝OCI SDK，沒有在GitHub安裝／執行這個READ1 runtime，沒有真實JWT／RPST、Oracle API、原生READ1 run或ChatGPT Oracle讀回。** 17方法不能代表這些。只核SDK官方介面／完整dependency graph，實際安裝／區域端點相容性仍待資格通過後首讀。Secret未由Codex建立／讀取，使用者側實際Secret值狀態未查，不宣稱不存在。

原Cloud／工程鎖／dev、原adapter／CTRL1 core／FM3 metadata90377／owner／main／880歷史檔保持；不建Oracle VM／volume／compartment、不付費／API key／搬FM3／交易／排程。原2026-11-05 native PING成功只沿用證據，不重讀全套／重跑。

完成原bytes GitHub保存後停止於**本人帳戶資格閘門**。只有本人前提成立、Secret與精確trust已設定，總監才發一次新的READ1命令並取得真實run／官方結果／遮蔽bot收據，再以ChatGPT工具讀回驗收；之前不標OCI_READ_CONNECTED。
