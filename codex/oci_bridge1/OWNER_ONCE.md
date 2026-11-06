# 停止舊API key／Environment Secrets步驟

M-OCI-READ1最新正式批准只涵蓋受限OAuth client credential進私人Repository Secrets。請只用[新的本人一次指南](../oci_read1/oauth_approved/OWNER_ONCE.md)，不照本文件下方建立長期API私鑰、Environment或其他憑證；也不重批已批准的儲存取捨。先核本人帳戶條件，未知即停。以下完整保留歷史，不作目前操作。

---

# 2026-11-05 暫停舊環境／密鑰設定流程

單次原生Actions探針已成功，證據見zero_budget_probe/README.md。GitHub Free私庫的原Environment Secrets方案已由使用者停止；不要執行下方舊環境／密鑰步驟，不要改存Repository Secrets。本輪結束，Oracle仍NOT_CONNECTED。以下只作歷史保存。

---

# M-OCI-BRIDGE1：本人剩餘操作一次說明

**私庫已建立並可讀寫，不要重建，也不用再批准。** 入口是 [private Issue #1](https://github.com/blue1998-glitch/Twstockai-oci-bridge-private/issues/1)。原Codex已把固定無憑證版本傳到私庫review/，不是要求本人逐檔搬運。現在尚未啟用Actions或Oracle查詢。

本文件集中所有本人不可替代的設定。只要任一停止條件不通過，就停在該點，不繼續設key，不逐張上傳截圖、不重跑CloudShell。不得將key、token、帳戶配置／OCID貼聊天或公開Issue。

## 一、GitHub Billing：先核實零付費，這項未通過不要做後面

1. 本人登入 https://github.com/settings/billing ，查看目前方案、Actions included usage／剩餘免費額度。只看帳戶自己的資料，不新增付款方式或升級。
2. 在Budgets and alerts／付費使用設定，確認Actions是否有**禁止額外付費使用**或0付費上限及到限停止的原生設定。僅email警示不算。若介面根本沒有能阻擋付費的選項，記為「無法核實」，不要啟用任何workflow。
3. 官方文件指出新預算不包含建立前用量，所以首期總費用可能超預算；不能只看新建0預算或本月0帳單就宣稱安全。需同時核實當期免費餘量、原有付費用量與新私庫的付費阻擋適用範圍。不要設定正數預算／付費runner，也不要刪別人的付款方式來解決。
4. 回報只需要這三項非敏感文字：**Actions免費餘量、付費使用目前是否已阻擋、畫面上該設定的名稱**。不需要卡片、帳號、私有JSON或每頁截圖。此為OWNER_OBSERVED，不冒充API讀回；原Codex還要核對是否足以安全執行，不能手動把成本旗標改True。

原GitHub App讀Billing與管理Actions均403，非授權未批准。未核實前保持沒有active workflow、沒有Actions run；不因私庫可寫就當作可零付費執行。

## 二、GitHub受保護環境（免費可用才設定）

1. 開私庫 https://github.com/blue1998-glitch/Twstockai-oci-bridge-private/settings/environments ，新增環境 **oci-read**。
2. Deployment branches／允許部署分支只限私庫main，限制能修改環境、workflow與Secret的人為本人及已批准的最小受信工程入口。原公開Twstockai main不動。
3. 若介面要求升級付費、顯示此方案不支援，停止，不升級、不改成公開庫或放寬保護。
4. 原App建立環境的PUT實測403，所以這個UI動作需本人；沒有要求擴大AI的私鑰讀取權。環境完成前不放Oracle key。branch保護、固定版本／concurrency／native事件驗證由原Codex繼續處理，不能只靠環境名稱當保護證據。

## 三、Oracle專用唯讀身分（前兩節通過，且原Codex確認可承接後才做）

1. 在Oracle本人控制台確認已有獨立 **pilot compartment**。若沒有就回報「沒有既存pilot」，停止：本授權不准新建compartment／VM，也不能改用root全域查詢。
2. Identity & Security → Domains →實際身分域，建立專用API使用者 **TwstockaiOciReader** 和群組 **TwstockaiOciReaders**，將專用使用者加入該群組。不要加入Administrators，不沿用自己的全權key。
3. 用Policies編輯器選實際身分域／群組及既存pilot。官方API表證明：ListInstances需要INSTANCE_READ；ListVolumes／ListBootVolumes需要VOLUME_INSPECT。政策只允許下面兩類操作（以實際域／pilot取代文字占位值，不給tenancy範圍）：

```
Allow group '<實際身分域>'/'TwstockaiOciReaders' to read instances in compartment <既存pilot名稱> where request.operation = 'ListInstances'
Allow group '<實際身分域>'/'TwstockaiOciReaders' to inspect volumes in compartment <既存pilot名稱> where any {request.operation = 'ListVolumes', request.operation = 'ListBootVolumes'}
```

不加manage／use／power／create／delete／IAM權限。若existing compute cluster等案例還需額外權限，先拒絕該範圍，不自行擴權。

4. 到專用使用者的API Keys → Add API Key，在自己的Oracle控制台／可信裝置產生key pair並下載private key。**不要在原Codex Cloud產生，不要傳給AI／Issue／Git。**
5. GitHub私庫 → Settings → Environments → oci-read → Environment secrets，由本人直接新增 **OCI_API_PRIVATE_KEY**，貼專用私鑰；官方API配置片段只由本人直接填 **OCI_CONFIG**。其餘pilot OCID／region／qualified AD清單也只放私有server設定，不放任何命令留言。若不知正確AD，保持未知，不加全租戶IAM權限補查、不另起CloudShell診斷。
6. 存好只回覆「專用唯讀身分與受保護Secret已設定」，不要貼值。這是設定回報，尚不是Oracle實讀成功。原Codex不得讀取Secret值；受信私有runner只在成本／來源／native授權全部通過後使用它們。

## 四、啟用與總監真正驗收（本人不用寫程式或再派工）

原Codex沿已批准範圍完成固定來源／依賴／私庫workflow設定，先無Secrets做native GitHub事件乾跑；任何缺失installation欄位、REST權限、OIDC claim或版本pin都fail-closed，不猜值／不降規。GitHub job OIDC只證GitHub來源，不能當OCI認證。

總監用已連接的ChatGPT GitHub工具，對private #1發原樣留言：

```
{"schema":"oci-read/0.1","operation":"list_pilot_compartment_resources"}
```

必須由Oracle真實回覆的遮蔽Compute／Boot／Block摘要讀回才結案。回覆不能含OCID、帳戶、IP、raw HTTP或私鑰。只有get_account_plan_kind可無原生API時維持UNKNOWN。未達真實讀回前永遠NOT_CONNECTED，不能以Secret已設或工程PASS取代。

## 撤銷與停止

本人可停用私庫Actions、撤銷專用Oracle API key或群組政策、取消連接器對私庫存取；不影響FM3或原owner。輪替在本人裝置產生新key→本人更新Secret→確認新key有效→撤舊key，不將任何key交AI。原Cloud資料不搬、不刪、不重啟，不建主機、不付費、不交易。
