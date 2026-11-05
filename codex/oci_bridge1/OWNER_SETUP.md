# 已批准橋接：本人必要操作集中說明

正式批准來源：Issue #2 comment 6647255490（2026-11-05）。不需要再批准相同範圍。本輪現有GitHub App身分的建庫POST回403；帳單用量API也403，不是使用者沒授權。**現在最少只須完成A：建立空private repo。** B/C集中列在此，未通過B不可設定key或啟用執行。不要逐張傳截圖，不貼token／私鑰／原始帳戶JSON。

## A. 本人建立空private repo（工具無法代辦的唯一建庫操作）

1. 開 https://github.com/new 。Owner選 **blue1998-glitch**。
2. Repository name填 **Twstockai-oci-bridge-private**，Visibility必選 **Private**。
3. 不選模板、不加入workflow、不啟用Codespaces／付費功能；按Create repository。若已存在就保留，不重建／刪除；確認Private即可。
4. 完成後回覆「私庫已建立」即可，不用貼任何憑證。原唯一Codex沿既有授權自動檢查能否讀寫新私庫、寫入固定版本及配置收件。原Cloud不clone第二工作目錄，不動公開main。

本次原有連接器安裝查得repository_selection=all，但這不是新repo可見性實測。總監仍須以原ChatGPT工具實際讀寫該私庫；若缺可見性，由本人到GitHub已安裝App設定，只授必要私庫範圍，不重新輸入token給AI。

## B. GitHub零付費／保護設定（核實前不要啟用Actions）

本人 https://github.com/settings/billing →查看方案、當期Actions剩餘免費用量、Budgets and alerts／付費使用限制。不要加付款方式、買runner、升級或設正數付費額度。只評估標準Linux runner、短時單次查詢、無artifact/cache與schedule；禁止larger runner。確認對此私庫／帳戶的付費Actions使用能被阻擋，並將paid usage維持0。

只有預算警示不夠；若介面可設0預算並Stop usage，也要確認本期先前用量與原有費用。官方文件指出預算建立前的用量不計入首期預算，因此首期總費用仍可能超預算；不能以新設0預算聲稱帳戶總費用保證0。Codex目前不能讀Billing（403），故此項UNKNOWN，**不得啟用workflow或把receiver的成本旗標改True冒認已驗證**。若無可查證的不付費中止能力，停在此處，不移除他人的付款設定、不買額度。

在私庫Settings → Actions先保持停用／不執行workflow；Settings → Collaborators限本人及既有受信App，禁止fork/PR不受信程式讀Secrets。固定審核SHA、收件Issue與actor，workflow concurrency須整個私庫單一執行群組，cancel-in-progress=false；使用checks持久消耗紀錄。環境／保護規則若此方案不支援免費，先回報，不升級或降低驗證。

## C. Oracle專用身分與key（B通過且私庫受保護環境可用後，集中一次做）

1. 在自己的Oracle控制台找到**既存pilot compartment**。若沒有獨立既存pilot，立即停止；本授權不允許新建compartment、VM或以root compartment替代。不要用主機數為0推定pilot不存在。
2. Identity & Security → Domains →目前身分域 →建立非人類API使用者`TwstockaiOciReader`及群組`TwstockaiOciReaders`。不要給Administrators／Console管理權限；API key是此身分專用，非自己的全權API key。
3. 在Policies以選取的身分域／群組及**同一個既存pilot**建立最小政策。依官方core policy表，ListInstances需要INSTANCE_READ（不是inspect instances）；ListVolumes、ListBootVolumes需要VOLUME_INSPECT。建議兩條操作約束，以下是須套用實際域／既存compartment的樣式，不可把占位值直接貼上或擴大到tenancy：

```
Allow group '<實際身分域>'/'TwstockaiOciReaders' to read instances in compartment <既存pilot名稱> where request.operation = 'ListInstances'
Allow group '<實際身分域>'/'TwstockaiOciReaders' to inspect volumes in compartment <既存pilot名稱> where any {request.operation = 'ListVolumes', request.operation = 'ListBootVolumes'}
```

這不允許GetInstance／power／create／update／delete／IAM變更。ListInstances本身可能含metadata，IAM不能只返回數量；受信執行器必須只在記憶體中投影，原件不進issue/log/artifact。遇compute-cluster額外權限需求先拒絕，不能自動擴權。

4. 在此專用使用者 → API Keys → Add API Key，在**本人控制台／可信裝置**產生並下載私鑰。這是唯一產生key的地方，不在原Codex Cloud、不在聊天或Issue。官方配置片段只由本人直接存進私庫受保護environment；私鑰直接存`OCI_API_PRIVATE_KEY` Secret，其餘配置存`OCI_CONFIG` Secret。不要把私鑰交給AI，不提交Git，不傳FinMind資料。
5. 執行器另需server固定的pilot OCID、region及qualified AD清單，存同一私有環境的配置；不接受命令傳入。不知道AD時保留UNKNOWN，不給租戶全域權限補查，不重啟CloudShell診斷。身分域／格式不符時停，不用自己的admin key代替。
6. GitHub Settings → Environments受保護設定只有本人能改，固定私庫／Issue／App installation／actor與workflow SHA。若原身分無權管理環境，由本人UI完成；不額外申請給AI讀私鑰的權限。

## D. 接收器與真正驗收（由原唯一Codex／總監做，不要求本人重複派工）

私庫、零付費及本人安全配置完成後，原Codex沿同授權繼續安裝固定receiver／真正REST/OIDC執行設定及依賴鎖，先做不帶OCI Secrets的native event dry-run。Actions OIDC只驗GitHub job身分，不當作OCI token交換。workflow簽章／installation／REST事件欄位缺失要拒絕，不能降為author_association；缺required claim或PyJWT則NOT_CONNECTED。

總監用原ChatGPT GitHub connector對指定private控制Issue送出下面原樣JSON留言（Issue尚未建立，不能猜入口或先向公開Issue送）：

```
{"schema":"oci-read/0.1","operation":"list_pilot_compartment_resources"}
```

成功必須取得OCI實際、只含Compute／Boot／Block數量及狀態的遮蔽收據，由GPT工具讀回；沒key／沒pilot／沒免費防護／沒真實事件驗證時，只能NOT_CONNECTED。get_account_plan_kind沒有受支持原生來源仍UNKNOWN，不把FreeTier口述當API回覆。

## 停止、撤銷與輪替

可先停用私庫Actions阻斷新查詢；Oracle刪此API key或移除此專用group政策即可撤銷，其他服務不動。輪替只在本人裝置產生新key→本人直接更新Secret→驗新key成功→撤舊key，任何舊key不發聊天。GitHub取消App對私庫的存取即可停止GPT入口；不刪Oracle／FM3資料、不搬原Cloud。
