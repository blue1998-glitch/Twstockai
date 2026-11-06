# M-OCI-CTRL1/0.2｜缺installation定向修復

部署已啟用；**新的原生PING驗收仍待總監，Oracle NOT_CONNECTED**。

私庫固定提交：`6015e6b834fcd24cf13f0b43648d76fa4c443cac`。控制器407700418 active，四部署檔逐bytes讀回一致；原probe保持disabled。完整版本／hash／讀回見[deployment.json](deployment.json)，實跑紀錄[tests.log](tests.log)。

## 已核根因

總監由ChatGPT連接器發出request6649866610；native run41969390096在原固定13e58a19787e9fb4ec55762a08ad10c930b34358失敗，Actions bot6649868699回REJECTED／NATIVE_INSTALLATION_MISSING。原件已實際讀取，原回應只留原Cloud Git外，不把摘要冒充完整私件。這證明事件與回覆通道存在，尚非PING_OK。

[官方契約與指紋](source.json)：issue_comment的installation只在配置並傳給GitHub App的webhook中提供，Actions GITHUB_EVENT_PATH不保證含該欄位。[總監原指令](INSTRUCTION.json)。

## 最小修復與保留防線

只建立無憑證 `PING_ONLY_NATIVE_ACTIONS_CANONICAL_REST` 判準。收據明示 `installation_attestation=NOT_ATTESTED`；不填入installation、不借舊ID、不將performed_via_github_app等同installation證明。原來release的installation_id不再作Actions原生條件。

固定private repo／Issue1／owner／來源App／canonical REST留言與當前write以上權限、native run的actor/event/path/ref/commit/attempt及workflow完整bytes仍全部核對。另核實triggering_actor、head_repository、repo.private及canonical active workflow ID/path。這些欄位已在真實失敗run取得，不是假設額外可用欄位。

256bytes嚴格兩欄JSON、未編輯5分鐘、未來拒絕、原始code SHA256/Git blob、短效token最小權限、2分鐘、全repo concurrency、完整bot收據nonce、STARTED→同則PATCH、未知結果不重送全部保持。不得以此無installation證明的信任擴張到Oracle/IAM/Secrets；其他operation一律拒絕。

## 本輪驗證

8唯一新方法通過：缺installation正例、偽造可選欄位不升格、owner/App/permission/private反例、替代native欄位與workflow缺失、非PING／錯誤安裝聲稱拒絕、code/time、舊REJECTED nonce不重放及缺profile/schema／sender拒絕。合成fixture不是原生成功。沒有重跑舊18方法／零費probe，沒有發新測試留言、rerun、workflow_dispatch或建立新native run。

部署前後native runs均2；原Issue留言2不變；新版本native驗收尚未執行。原失敗證據保持，沒有改oracle資格、來源、策略、原FM3或owner服務；沒有配置憑證、Secrets、帳單或Oracle資源。

## 總監唯一下一步

使用ChatGPT已連接GitHub工具，在[私人Issue #1](https://github.com/blue1998-glitch/Twstockai-oci-bridge-private/issues/1)新增一則下方**純JSON**，不要code fence或重用舊留言：

```
{"schema":"oci-ctrl/0.1","operation":"ping"}
```

讀回新request ID、native run completed/success、bot PING_OK；workflow_commit_sha須為 `6015e6b834fcd24cf13f0b43648d76fa4c443cac`，controller_version=M-OCI-CTRL1/0.2，handler SHA256=825a8fc1e0e6e86be801f962d0c039f6c9e5b4c7ce9cb83772ff48c88525bb44，installation_attestation=NOT_ATTESTED，Oracle NOT_CONNECTED／0 calls。收據STARTED／REJECTED或本地測試PASS不能當驗收。舊6649866610已消耗，不可重用或rerun。

只有這次總監親自讀回成功後，才標GPT_TO_GITHUB_RUNNER_CONNECTED；本輪不延伸到Oracle憑證。
