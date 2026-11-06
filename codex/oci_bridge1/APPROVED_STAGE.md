# M-OCI-BRIDGE1 正式批准後工程：客觀權限阻塞

**NOT_CONNECTED。授權已核，不再要求重批。** 固定授權原件APPROVAL.json。原Cloud／工程鎖／dev／FM3／owner及main保留，沒有建Oracle資源、設定或讀取本人私鑰。新private repo的POST實際403 `Resource not accessible by integration`；查Billing用量也403。GET private repo 404只表示本身分不可讀，不能證明全域不存在；本輪建庫未成功，沒有實際私庫／workflow入口可報。

## 這輪已做

重用既有16方法樣機與原生SDK adapter（未重跑歷史16）。新增receiver.py：GitHub Actions job OIDC RS256／issuer／audience／時間與必要claim驗證，固定workflow SHA/ref／private repo／actor／installation，再以canonical GitHub REST核comment／App／Issue／協作者權限與未編輯／5分鐘。只收兩個固定JSON動作，不接受任意URL／Shell／compartment。OIDC不是OCI認證，不偷渡新key。

GitHubRest只有固定GitHub API path；所有URL均由server repo設定與數字ID組成，不使用body URL。PersistentChecks以不可變comment ID衍生nonce，對固定SHA全頁查checks後先登記再發OCI，跨run相同nonce拒絕；必須與私庫workflow單一concurrency群組一起啟用，不聲稱一般多主機原子鎖。未知建立check結果不自動重送。投影後收據可寫check或指定private issue，不回原件／OCID／例外內容。

13唯一新方法實跑通過（初批10／最後13不加總）。簽章錯誤拒絕、native metadata mock、REST fake、跨handler replay及費用未知前零factory／零Secrets測試。**沒有真實GitHub job JWT／private REST／cross-run workflow或OCI測試。** PyJWT／OCI依賴未安裝為生產環境，沒有wrapper自動讀secret；實際workflow／native event dry-run尚未配置。receive_safe僅回固定拒絕碼，發生晚期例外時query狀態UNKNOWN，不謊稱0查詢。

## 費用及目前硬停點

GitHub帳單API拒絕，不知目前免費餘量／付費阻擋是否可用；公開官方文件只能證一般規則。官方Budgets文件指出建立前用量不計入首期，不能只用警示或新設預算保證整個帳戶0費用。因此現在不啟動Actions、私有runner、schedule或任何雲端執行；receiver成本閘門default False，是未接通的整合邊界，不能人工改True當證據。

不是僅差貼OCI key：私庫／安全設定與免費防護仍需先通過。未知installation event欄位或原生REST權限不能以猜值通過；真實worker及OIDC依賴鎖須於私庫及費用解阻後安裝、先無Secrets核實。這些未實作／未配置項不可標完成。

## 本人僅需的一次建庫操作與集中安全設定

[OWNER_SETUP.md](OWNER_SETUP.md)整份集中列出建立空private repo、免費／保護設定、專用最小唯讀IAM／私鑰直送Secret、總監真實驗收及撤銷。現在只需 https://github.com/new 建立 blue1998-glitch/Twstockai-oci-bridge-private，必選Private、不要workflow／付費選項；回覆私庫已建立即可，原Codex在同授權下接續，不需重新派工。B未通過先不放key。當前實際入口仍NOT_CONNECTED，不重做CloudShell／FIDO或股票UI。
