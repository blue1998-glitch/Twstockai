# 固定提交逐檔GitHub回讀

本輪產品固定提交：`f1b9468b0d789bb7930964886ed5dc34c30e758e`。
基準 `0d6e86a57b8ce2d4f20244f50ee0ee8d29f6ce62`、正式0.4 `dae1f6e580f466c4f44cb271a350f4b420d5b5eb`及全部後續完整保留。

於2026-10-23T06:08:09.850641+00:00，55個變更檔逐一從固定提交raw.githubusercontent.com讀回，全部HTTP200、完整bytes／SHA與git show相同，包含新程式、PDF原件、抽字、PNG、測試／失敗證據、22,611,030bytes ZIP及根交接。詳見[GITHUB_READBACK.json](GITHUB_READBACK.json)，不是只核分支檔名或本地雜湊。

同時遠端分支頭為產品固定提交；main仍為 `9c5b168c09ba80010c74f03b9c537e8b7474256a`。只有此既有Codex工作寫入，無平行工作、強推或main變更。此收據另正常提交，避免收據自指提交雜湊；最新提交請查分支ref，兩收據的實際回讀在收尾另核。

下載 [ZIP](m1-source-diagnostics-v05-20261023.zip?raw=true)、[SHA256SUMS](SHA256SUMS)、[封包實測](package-verification.json)及[入口](README.md)。ZIP SHA256：`7144793cb2e359b7536fa72dd2c764144e4aee4a6aa3e986eabcaa785435a36d`。

61項＝30新診斷＋31正式回歸，完整checkout與新解壓各實跑；原528成員及新舊七manifest保持。70窗拒算、2不足、8換股未支援、真正總淨報酬合格0。未取得兩停牌起日及法律原件，兩缺價原因UNKNOWN／Raw null保持；公司非個人淨到款，無新UI／Android或六方案。

下一步Work只作來源研究與GitHub唯讀，完整可貼指令：[WORK_HANDOFF.md](../../股票系統M1_v0_18/rotation_research/source_diagnostics_20261023/WORK_HANDOFF.md)。不bootstrap／工程／測試／commit／push，不開第二個Codex寫入。工程仍回既有唯一Codex重新核遠端、bootstrap成功後執行。
