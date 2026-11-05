# M-OCI-CTRL1｜已啟用，等待總監第一次真實PING

**部署狀態ENABLED_AWAITING_DIRECTOR_PING，不是GPT_TO_GITHUB_RUNNER_CONNECTED。Oracle始終NOT_CONNECTED／0呼叫。** 本輪指令來源INSTRUCTION.json（公開Issue #2 comment6649248101）。原Cloud／工程鎖／dev、FM3、owner8765與公開main保持。

## 總監唯一驗收動作

在原已連接ChatGPT GitHub工具，對[私庫Issue #1](https://github.com/blue1998-glitch/Twstockai-oci-bridge-private/issues/1)新增**一則原樣JSON留言，不加Markdown code fence**：

```
{"schema":"oci-ctrl/0.1","operation":"ping"}
```

Codex未代發任何測試留言，也未重跑原生零預算探針。總監發送後等native Actions完成，再由同一GitHub工具讀回Actions bot收據，確認status=PING_OK、request_comment_id等於該新留言ID、run_id/run_url對應原生issue_comment run且conclusion=success，核固定版本；之後才可標GPT_TO_GITHUB_RUNNER_CONNECTED。STARTED、REJECTED、skipped或單純工程PASS都不能當完成。不要用人工留言補PING_OK。

## 已核固定部署

私庫commit **13e58a19787e9fb4ec55762a08ad10c930b34358**；workflow `.github/workflows/ctrl1.yml`，id 407700418、state active。workflow Git blob **c229a46d562058530afd23109957110018dee9ff**；handler SHA256 **92fd8bb867c253e000440ff4f051dce0c5ef4c6116aa03b151447e92c62200d2**。原bytes讀回4檔。完整非敏感摘要deployment.json，含實際runner/timeout/permissions。伺服器App/installation綁定只存私庫release.json／原Cloud Git外，不公開個人配置。

標準ubuntu-24.04，2分鐘，一個全repo固定concurrency group、cancel-in-progress=false；GitHub原生只保留一個pending的限制仍存在，這不是無限可靠佇列。權限僅contents:read、actions:read（核真native run）、issues:write（收據與nonce）。只有一步用平台短效github.token，不讀repository/environment Secrets、不用外部Action／套件／checkout、無artifact/cache。未變更US$0付費預算，沒有其他服務／部署／Oracle身分／私鑰或交易。

GitHub原生issue_comment訂閱在repo層；job if在分配runner前限私庫ID1446437252、Issue1、owner actor319797247、created且不是PR。非scope事件只會skip，程式再次以原生event＋authenticated GitHub REST驗repo/actor/role、App、native installation、run id／attempt／commit／時間與canonical comment。沒有獨立webhook HTTP入口，也不將HMAC fixture當native身分認證。

## 版本與收件規則

只有schema=oci-ctrl/0.1及operation=ping兩欄，允許JSON外部空白，拒絕重複key／額外欄位／URL／CLI／Shell／OCID／compartment及非PING。canonical comment須未編輯、非未來、5分鐘內，來源App與owner必須一致，author_association不能代替ID／REST權限。

handler由不可變private Git blob下載，執行前驗SHA256與Git blob。handler再由自身原bytes重建**唯一允許的完整workflow bytes**，與native workflow commit內的檔案逐bytes核對；不是只相信同commit的release自稱hash。原生run/head/workflow SHA、path/ref/repo/actor及attempt1皆需一致。第一次驗收請核上方固定commit；任何日後版本改動都要重新核部署版本。

native event缺installation欄位時回REJECTED／NATIVE_INSTALLATION_MISSING，錯值則MISMATCH；不猜值／借舊值放行。canonical API或必要權限缺失亦fail-closed。此原生事件相容性仍待總監首輪真實測試，不能以fixture通過宣稱所有欄位已實證。

## 跨run重播與收據

以不可變request comment ID作nonce，不接受caller傳入nonce。全頁掃Issue bot收據；不完整／超1000留言則拒絕，不截斷當沒有。只認本次部署實讀的GitHub Actions bot及App來源，owner自己複製marker不當作有效收據。

在PING前POST一份STARTED bot收據作持久消耗標記，再PATCH**同一則**為PING_OK；跨run同comment已存在任何收據即DUPLICATE_NO_ACTION，run_attempt>1一律拒絕。網路未知結果不重發POST/PATCH，不把僅終點一致當全部途中已核。原生concurrency確保單一合法job，GitHub_TOKEN事件自觸發抑制＋actor filter避免回覆循環。

收據schema=oci-ctrl-receipt/0.1，含status、controller_version、request_comment_id、run_id、run_url、run_attempt、workflow_commit_sha、workflow_blob_sha、controller_sha256、oracle_status=NOT_CONNECTED、oracle_calls=0。拒絕有固定reason，沒有原body／錯誤原件／token／OCID。授權成立但schema/installation不合的owner請求可收到REJECTED；更早的身分或API失敗僅在job輸出安全拒絕碼，不回覆不受信對象。

## 本輪實測與未驗

18個唯一新方法實跑通過，涵蓋原生metadata/REST **fixture**、成功post→patch、缺安裝欄位、scope/版本/過期、fake marker、replay、未知網路不重試及workflow exact bytes/權限/bootstrap編譯；初批15及中間18不累加，舊測試／原生probe未重跑。這不是ChatGPT觸發驗收，controller native runs仍0，沒有真實PING收據。

只有無憑證PING，不是Oracle金鑰隔離安全設計；私庫code寫入者仍為信任根，GitHub Free缺原環境／分支保護不能被此功能掩蓋。沒有新Secrets／Oracle SDK／OIDC交換／主機／FM3搬遷，不擴張下一工作。保存／讀回後停止，交總監親自首測。
