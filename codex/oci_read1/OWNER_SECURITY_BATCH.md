# M-OCI-READ1｜唯一安全方案與本人一次集中授權

**此為待核方案，不是已啟用設定。不執行舊OWNER_ONCE／Environment Secrets步驟，也不改存Repository Secrets。**

## 一個方案：既存隔離OCI主機＋一次性self-hosted runner＋Instance Principal

沿用私人Issue／native Actions／固定版本與現有SDK adapter，把真正的OCI讀取放到本人控制的**既有**、無FM3的隔離Oracle主機，以Instance Principal取得平台自動輪替的短效憑證。不新增OAuth client secret、API key或GitHub Repository Secret；不在原Codex Cloud放Oracle身分。runner只向GitHub連出，不需要新增公開網站／入站入口。此為待批准的執行位置變更，不是本輪已取得的權限。

必須先由本人確認現有主機、既存pilot、免費資格、實際剩餘額度與隔離條件。**目前沒有帳戶原件可確認這些條件。沒有既存合格免費主機／pilot時本方案不可執行，保持BLOCKED；不新建主機、compartment、磁碟，不升級或依賴試用額度。** 不以此方案文字宣稱可零成本直接上線。

## 本人集中處理的全部項目（核准前不執行）

1. 核准這一個具體方案，確認可使用的既有隔離Always Free主機與既存pilot。帳戶識別／OCID只留本人控制台及未來主機私有設定，不貼聊天或公開Issue。沒有符合項就只回覆「沒有合格既有主機／pilot」，不嘗試其他計費資源。
2. 本人以管理身分在Oracle設定**只匹配該一台主機**的dynamic group；移除／排除它繼承的其他多餘應用權限。對既存pilot僅授予ListInstances所需INSTANCE_READ、ListVolumes與ListBootVolumes所需VOLUME_INSPECT，以request.operation限制三個List操作。不授予manage/use/create/update/delete/power，group不匹配整個compartment或tenancy的所有主機。這些是本人管理授權，不由現有GitHub程式代做。
3. 本人確認並接受下節的Instance Principal固有權限與runner風險；不接受就停止，不能用新的flag忽略。
4. 核准後才由原唯一Codex完成**獨立READ1**固定版本、native來源與短效job身分驗證、私庫Issue1／owner／App／workflow SHA與完整bytes、時間窗、持久nonce、受控單次排程、服務身分綁定及無重試32請求上限。owner在私庫Settings → Actions → Runners中親自完成一次性、最小repo範圍runner註冊；不能把註冊token交AI、聊天或Git。啟動命令／受信bundle需在該授權後由Codex固定並校驗，不提前執行未封版安裝命令。這不是讓本人下載FM3或自己編寫伺服器。
5. pilot／region／AD清單由本人在新隔離執行位置一次綁定，原始配置保持私有。沒有證據不給額外tenancy IAM讀取權補查，不猜AD、不把root當pilot。原Codex只核非敏感配置收據，不讀任何秘密值。
6. 完成上述設定後，總監才透過原ChatGPT GitHub工具新增固定READ1命令。必須取得新native run與Oracle真結果／可核官方拒絕、脫敏bot收據後才宣告OCI_READ_CONNECTED。驗收後撤銷一次性runner註冊、停該讀取程序；不停止／刪除其他Oracle資源。撤銷dynamic group政策會解除本方案的應用讀取權；平台固有compartment_inspect另見下節。

上述是**一次整批授權／設定說明**，不是要求逐張截圖或每步回傳。現階段唯一需要總監／本人決定的是第1項的方案與既存主機條件；批准前Codex不註冊runner、不改IAM、不加入憑證或workflow權限。

## 必須明示的剩餘風險

- Oracle官方明載：Instance Principal固有`compartment_inspect`不能撤銷，可列租戶compartment名稱／說明等；所以**不能稱它是絕對僅pilot的身分**。本方案只讓應用呼叫pilot三個List，但身分仍有上述平台固有可視性。若此範圍不能接受，本方案不成立，不自動切換API key或Repo Secrets。
- 任何能控制主機的使用者／程序會繼承Instance Principal權限。GitHub官方警告self-hosted runner可能被工作流持久入侵。必須是獨立低權限主機，不放FM3／其他服務憑證，不能在原Codex環境註冊；一次性runner不是主機安全的保證。
- 私庫程式寫入者和主機管理者仍是信任根。Free私庫缺受保護Environment Secrets／分支保護的問題沒有被PING成功解除；固定bytes、owner／App驗證、短效憑證與一次性執行縮小風險，不能聲稱消除惡意維護者風險。
- 本方案不需要長期OCI API key，但runner自己的GitHub註冊／執行憑證仍是秘密，必須留本人控制的隔離主機，不能進Git或回覆。Oracle帳戶資格、主機費用、既有權限、SDK依賴與端點尚未實核；不成立即停。

官方依據：[Instance Principals](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm)、[GitHub self-hosted風險](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions#hardening-for-self-hosted-runners)。本輪抓取指紋見sources.json。
