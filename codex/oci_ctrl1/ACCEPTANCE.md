# 總監可直接操作的驗收

1. 用ChatGPT已連接GitHub工具，在blue1998-glitch/Twstockai-oci-bridge-private Issue1貼**純JSON**：

```
{"schema":"oci-ctrl/0.1","operation":"ping"}
```

2. 等原生Actions完成，再讀該Issue的bot收據；不要把STARTED當成功。預期status=PING_OK並有request_comment_id、run_id/run_url、固定workflow commit/blob、controller SHA，Oracle仍NOT_CONNECTED。
3. 讀native run核event issue_comment、conclusion success，與自己的留言ID／部署版本一致。未通過時讀安全reason／job拒絕碼交原Codex修復，不人工補成功、不跳過安裝或API驗證。
4. 工程已啟用但總監尚未發送／讀回之前，不標GPT_TO_GITHUB_RUNNER_CONNECTED。本輪不收Oracle key，不啟任何其他operation。
