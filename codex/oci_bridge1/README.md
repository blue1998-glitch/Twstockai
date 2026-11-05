# 2026-11-05 最新入口｜READ1身分隔離受阻

PING控制通道已由總監原生驗收成功，不能稱舊橋接全未連線。真正OCI仍NOT_CONNECTED；最新[READ1無密鑰工件](../oci_read1/README.md)、[本人唯一安全方案](../oci_read1/OWNER_SECURITY_BATCH.md)。舊adapter保持原bytes，舊receiver／Environment Secrets／API key配置不啟用、不改存Repository Secrets，不重跑舊套件或PING。下方歷史不是目前執行指令。

---

# 2026-11-05 暫停舊環境／密鑰設定流程

單次原生Actions探針已成功，證據見zero_budget_probe/README.md。GitHub Free私庫的原Environment Secrets方案已由使用者停止；不要執行下方舊環境／密鑰步驟，不要改存Repository Secrets。本輪結束，Oracle仍NOT_CONNECTED。以下只作歷史保存。

---

# 2026-11-05 最新入口：私庫已交付

請先讀PRIVATE_STAGE_HANDOFF.md與OWNER_ONCE.md。私庫已建並可讀寫，不重建／不重批；以下保留前輪歷史，不當本輪待辦。

---

# 2026-11-05 正式批准後最新狀態

[APPROVED_STAGE.md](APPROVED_STAGE.md)：授權已取得；private建庫與Billing均403，實際NOT_CONNECTED。13本輪receiver方法不冒實際橋接；舊16為前輪紀錄。[本人集中操作](OWNER_SETUP.md)，不再逐張上傳或CloudShell診斷。下方原樣機歷史保留。

---

# M-OCI-BRIDGE1 — Issue #2

**NOT_CONNECTED。只完成無憑證、未啟用的最小樣機；沒有Oracle實讀或GPT端到端驗收。**

入口 `python3 -m codex.oci_bridge1.bridge` 實際回報NOT_CONNECTED。唯一工程Cloud／dev分支／工程鎖依M-UNIFY1；原FM3、owner8765、main、部署工具歷史不動。本目錄不讀它們、不啟服務、沒有workflow、Secret或雲端資源。

## 可執行的協定與OCI讀取器

`bridge.py` 是獨立無網頁核心：有界嚴格JSON → HMAC受信通道 → 固定私有repo數字ID／installation／actor白名單／固定40字元commit／分支／事件／5分鐘有效期 → Git外私有重播日誌 → 固定OCI SDK read map → 僅數量與允許的狀態彙總。請求不能提供compartment、AD、URL、Shell或其他程式。封裝簽章須由未來受信接收器在核實GitHub原生事件＋REST身分／私有倉庫後產生，不能簽使用者自稱的metadata。**目前HMAC只在合成測試使用，並非已驗GitHub原生認證、GitHub OIDC換OCI憑證或遠端App。**

兩動作：`get_account_plan_kind` 無受支持的API證據時只回UNKNOWN（目前不發API，不借本人FreeTier陳述）；`list_pilot_compartment_resources` 僅由server設定的pilot compartment/AD列compute、boot、block。來源／key／OCID不從請求收取。正式SDK factory設定官方region endpoints、NoneRetryStrategy、connect/read timeout 5/15秒；每次32個list請求、每類最多500資源、每序列16頁，不足或循環／例外是UNKNOWN，不補0。預設SDK不安裝／不連線，factory未實際使用。

回覆只投影允許的count/state欄位，不回OCID、帳戶、人名、IP、tag、HTTP原件或錯誤內容。成功空清單只能來自SDK明示list，並非CLI空白補零。失敗不證資源不存在。只涵蓋pilot，不聲稱租戶全盤。

## 實際測試與限制

16唯一新方法通過（初批14與最終16不累加）；全部是本地協定／合成SDK／簽章／私有重播保存測試，不是OCI實際授權或讀取。測過錯身分／公開repo／錯installation／版本分支commit／未來過期／重播／額外欄位與任意命令／簽章錯誤／私有輸出／SDK錯誤未知／分頁循環／上限。真實Oracle讀取0，新的GitHub工具呼叫0。

本對話目前只有Cloud環境工具，沒有可呼叫的GitHub或Oracle connector；Git shell push與讀公開Issue不能代替已連接的GitHub工具驗收。無OCI credential/outbound identity；不能將另一對話的GitHub能力視為本對話可用。

ReplayStore只用單一私有主機的受鎖日誌，1024筆後拒絕，不自行清空。GitHub-hosted runner跨次執行不持久；**啟用前必須完成私有、受信、可持久／可序列化的消耗紀錄與事件驗證整合**，不能直接上Actions就聲稱防重播已落地。沒有HTTP/webhook/general-purpose endpoint或公開workflow範本可誤啟。

## 下一步與停止

只提交此無憑證樣機及證據，按Issue授權邊界停止。批准事項見AUTHORIZATION.md；批准前不建private repo、IAM身分或Secret。後續真實驗收必須由總監在已連接工具送出允許命令，收到OCI實際的遮蔽彙總，核固定版本與request id。未達前持續NOT_CONNECTED；不回Cloud Shell／FIDO／截圖流程。
