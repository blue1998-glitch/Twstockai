# M-OCI-READ1｜本人一次集中操作指南

**OAuth Repository Secret安全取捨已正式批准，不需要再次批准。** 不使用長期OCI API key，也不回舊自管主機／Environment Secrets／CloudShell診斷流程。本指南的步驟有先後閘門；未知就停，不為了完成而照填確認。

## 目前唯一需要先做的事：核本人既存Oracle條件（全為查看）

1. 登入自己的Oracle控制台。右上區域選單確認實際區域；租戶資訊核Home Region。左上選單 → Identity & Security（身分與安全）→ Domains（網域）→ **既有**身分域。Overview／Domain information查看Domain type，必須實際為**Free**；租戶Plan Type的Free Tier不等於該身分域的Free。不要按Change domain type／Upgrade或建立另一個domain。
2. 在該身分域查看Identity Propagation Trust／對應Workload Identity Federation功能及現有物件／剩餘額度。官方Free表列OAuth third-party token管理可用、Identity Propagation Trust總上限30且Free域不使用meters；這不是本人剩餘額度或所有區域已啟用的證明。必須是**Resource subject、JWT→OCI RPST／Control Plane**，不能只看到JWT→OAuth access token就確認。若控制台沒有此功能，或需升級／計費，停在此處，不建client、不輸入Secret。
3. Identity & Security → Compartments，確認**已存在的獨立pilot compartment**。本輪不建compartment，不改用root。再由本人／Oracle管理者核實該WIF Resource principal的實際IAM映射，只允許pilot內`ListInstances`所需INSTANCE_READ，以及`ListVolumes`／`ListBootVolumes`所需VOLUME_INSPECT。不要用全租戶read/manage、Administrators或未核的any-user範本。此帳戶的principal／domain條件尚未取得，因此本交付沒有可冒充通用正確的IAM語句；若管理者不能確認精確條件，`minimum_list_iam`保持UNKNOWN並停，不嘗試擴權。
4. 本人查看GitHub的Actions免費剩餘與原US$0付費阻擋仍有效；不調高預算。私庫Settings → Collaborators確認僅授權寫入者；Actions看現有workflow。Codex本輪API實讀只有1個collaborator，原兩workflow均沒有Secret引用；新READ1只有一個必要Secret引用。**Repo Secrets無法真正限制到單一workflow**；目前或日後能修改workflow的人可能取得它，固定SHA／預檢不是environment approval／branch protection替代品。此風險已批准，這裡只是核實現況，不重批。

任一項不成立，只回報安全文字（例如「Free domain未核／WIF未開放／沒有獨立pilot／精確IAM未知」），不要傳OCID、私有JSON、密鑰或敏感截圖。這是本輪的實際停止點，不是要求重跑PING或Oracle診斷。

## 以上全部成立後，才在同一次設定中繼續

5. 在同一既有Free身分域：Integrated applications／Applications → Add application → Confidential application，建立專用runtime client。**runtime client不得有Identity Domain Administrator或任何管理App role**；只把它列為此IdentityPropagationTrust允許的OAuth client。不把用於管理trust的高權限client Secret交給GitHub；建立trust由本人互動管理身分處理。核剩餘免費app／trust額度；若介面要求付費或無對應功能立即停。client Secret只在本人控制台留存，稍後直接輸入GitHub Secret。
6. GitHub私人倉庫 → `read1/oauth/account.json` → 鉛筆Edit（不要在公開庫）。本檔已放好唯一JSON骨架。本人依實際頁面填：
   - `captured_at`為本次真正核讀時間、`expires_at`最多24小時後，兩者用含時區ISO格式，例如`2026-11-05T15:00:00+08:00`；不要照抄範例日期當實際核讀。
   - `observations`填本人看到的Free域、WIF與實際區域、pilot/IAM、額度／US$0、寫入者簡短紀錄；只能寫真正已看到的內容。不放client Secret、API私鑰或token。
   - `findings`僅把已核實項改為`OWNER_CONFIRMED`；任何不知道的仍UNKNOWN，程式會擋住。`repository_secret_risk_accepted`已依正式批准預填，不需重批。
   - `config.domain_url`從既有domain Overview複製官方HTTPS URL（本版只接受`https://idcs-....identity.oraclecloud.com`，不要加結尾斜線／任意自訂網域）；`client_id`為專用runtime client ID；`region`為真實OCI服務區域；`pilot_compartment`為既有pilot的OCID；`availability_domains`為本人核實的完整相關AD名稱清單。這些只留私庫，不貼聊天。沒有完整AD證據就停，不加tenancy IAM讀取權補查。
   - 其他schema/source/config_binding原樣保留，Commit到私庫main。本檔同時保存觀察與設定，執行器從**同一不可變workflow commit**讀取並自行算SHA，不要求本人計算雜湊或跑終端。
7. 完成私庫最後一次設定commit後，複製**完整40字元main提交SHA**。Oracle建立／核對該domain的IdentityPropagationTrust：type JWT、subjectType Resource、issuer `https://token.actions.githubusercontent.com`、publicKeyEndpoint `https://token.actions.githubusercontent.com/.well-known/jwks`；allowImpersonation true、impersonatingResource `githubactions`，oauthClients僅包含runtime client。以該區域實際支援欄位核對，缺功能不猜。
   - 最多5條`claimValidations`全部精確比對：`repository_id=1446437252`；`workflow_ref=blue1998-glitch/Twstockai-oci-bridge-private/.github/workflows/read1.yml@refs/heads/main`；`workflow_sha=剛才的完整私庫SHA`；`event_name=issue_comment`；`aud=twstockai-oci-read1`。
   - 程式另以GitHub固定JWKS驗RS256、exp/nbf/iat、私庫、actor_id、sub、ref、run_id/attempt，以及canonical owner／來源App／REST權限。預期sub為`repo:blue1998-glitch/Twstockai-oci-bridge-private:ref:refs/heads/main`；這仍待首個真實READ1 JWT核實，若不符就安全拒絕，不能改成萬用字元。
   - 不需要增加claimPropagation或建立新OCI資源來湊條件。若實際IAM映射需要額外已核欄位才能限制pilot，由Oracle管理者核實；不放寬為全租戶。任何私庫新commit都必須重新審核並更新Oracle精確workflow_sha，不能用main移動名稱代替SHA。
8. 僅以上條件全部成立且固定workflow已審閱後，私庫Settings → Secrets and variables → Actions → **Secrets** → New repository secret，名稱 **`OCI_READ1_CLIENT_SECRET`**，本人從Oracle直接貼專用runtime client secret。不要貼給AI、Issue、Git、日誌或任何中介頁。除此之外不設定API key、管理client secret或舊OCI Secrets。
9. 同頁**Variables** → New repository variable：`OCI_READ1_ENABLED`＝`OWNER_REVIEWED_ONCE`。這是最後啟用動作，不能在前提未知時先設定。Actions → 原M-OCI-CTRL1 private PING →選單Disable workflow，避免它把READ1命令另外當非PING拒絕；不刪原檔／歷史、不重跑PING。新READ1 workflow已註冊，原始預設閘門關閉；不需要Run workflow，也沒有workflow_dispatch／schedule。
10. 本人只回覆「資格及安全設定已完成」即可，不回值。之後總監以已連接ChatGPT GitHub工具，在private Issue #1發**一則新純JSON**：

```
{"schema":"oci-read/0.1","operation":"list_pilot_compartment_resources"}
```

總監讀回新的native run、`OCI_READ_OK`／有明確官方拒絕的收據、request id與固定版本才驗收。`AUTHORIZED`／`EXCHANGING`只是持久nonce狀態，不是成功；若安裝／網路中斷會保留未知狀態，不重跑舊run或重用留言。Secret已設定／15工程測試通過都不是OCI連線。

## 保護、上限與撤銷

來源只限私庫#1固定owner／App與固定兩欄命令；兩階段job、授權及資格／nonce先於Secret步驟，Secret僅最後讀取step。GitHub短效OIDC→官方`/oauth2/v1/token`，`requested_token_type=urn:oci:token-type:oci-rpst`，短效RSA簽署金鑰只在RAM、RPST請求5分鐘；不讀長期OCI API key、不輸出raw token或回應。TLS驗證開啟、禁止redirect與重試；原SDK最多32個list、每類500資源／16頁，實讀另有90秒期限；GHA授權job2分鐘、讀取job4分鐘、同repo單一concurrency。免費餘量不足時US$0阻擋仍不得解除。

本人可先刪／停用`OCI_READ1_ENABLED`或Disable READ1 workflow，再於Oracle停用專用client／輪替client secret／移除該trust的oauthClients與pilot唯讀政策。更新Secret只由本人直送；不要刪除其他資源，不影響FM3／原owner。取消variable不是密鑰撤銷，真正撤銷需Oracle停用client。帳戶證據超過24小時自動拒絕；要續用必須重新實際核讀，不自動續期限。
