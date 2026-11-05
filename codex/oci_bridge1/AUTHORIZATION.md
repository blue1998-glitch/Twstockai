# 2026-11-05 最新入口：私庫已交付

請先讀PRIVATE_STAGE_HANDOFF.md與OWNER_ONCE.md。私庫已建並可讀寫，不重建／不重批；以下保留前輪歷史，不當本輪待辦。

---

# 已於2026-11-05正式批准

授權來源APPROVAL.json／Issue #2 comment6647255490。下方是已批准原案，不再要求重批；執行狀態見APPROVED_STAGE.md。

---

# 給總監的一次性重大授權案（尚未執行）

Issue #2允許無憑證樣機，但明確要求在新private repo／Oracle專用身分／加密Secrets前批准。以下不是已建立資源。

請一次批准此界定範圍：

1. 建獨立 **private** `blue1998-glitch/Twstockai-oci-bridge-private`，只存受信控制程式與遮蔽收據，不存FM3、Oracle原件或私鑰。原公開Twstockai不加任何workflow或OCI secret。固定已審核commit，保護分支，限制唯一維護者／接收actor及issue，不接受PR/fork任意內容；workflow只執行固定JSON動作，不將issue正文拼進命令。先確認私人Actions免費分鐘／可用額度，必要時設定零額度即停；不開付費runner、定時任務或公網服務。
2. 在Oracle建專用非人類API唯讀身分／群組，僅允許本次**既存pilot compartment**所需Instances／Boot／Block列舉，不給全租戶manage／IAM修改／Compute create／action。若無可隔離的既存compartment，先回報，不借此授權建機或擴大成根租戶盤點。具體permission名稱先核官方支持才部署；可隨時停身分與撤銷API key。
3. 使用者一次性在自己的可信裝置／Oracle控制台產生簽署金鑰，直接交給私人repo受保護environment secret或另經批准的加密secret manager。**不經聊天、Issue、原Codex Cloud、Git或原始日誌。** 不啟用OCI寫權、不買服務、不搬FM3。只保留最小必要meta及旋轉／撤銷程序。GitHub OIDC不能臆稱原生換OCI token。
4. 授權ChatGPT GitHub連接器存取此private repo，至少能送出及讀回指定issue命令／收據；實際工具權限確認後才定最後接收方式。當前本對話無該工具，不保證核准repo就會自動出現。接收器須驗GitHub原生事件、精確repo/installation/actor、REST權限與事件內容，不以author_association判斷；配置前先實作跨run持久防重播／序列化與封存讀回。嚴格限制issue write收據權，其他GitHub權限最小化，任何取消／quota不足／來源不明都停。

成本：目標只用已核GitHub免費執行額度與OCI唯讀API，不建Oracle VM／Volume，不靠試用抵扣。實際免費執行額度尚未查核，不能保證或開付費上限。風險：長期簽署key及IssueOps可能洩漏權限；以最小scope、私有隔離、固定SHA、窄權限、零原件日誌、限制actor、旋轉撤銷及用量中止降低風險。憑證輪替／接收主體改變需重新核信任，不借此次啟用寫入。

批准後集中一次安排本人登入／金鑰直送secret及connector選repo；不要求逐次登入或上傳截圖。可以撤回批准而停用接收器、撤銷key／連接器權限；不刪私人資料。取得新授權前只保留可審樣機，實際狀態NOT_CONNECTED。
