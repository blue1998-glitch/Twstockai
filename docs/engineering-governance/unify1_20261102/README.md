# M-UNIFY1｜唯一工程入口與環境規則

**唯一工程對象：目前這個已完成 M-PORT1、實際讀到 FM3 的既有 Codex 對話。** 不能以同名「Twstockai」對話或相同 `/workspace/Twstockai` 路徑代替身分核對。Work只讀研究，總監派工與驗收；其他歷史Codex對話不再接受工程寫入任務，但不得刪除、封存清理環境或假稱平台已強制停寫。

| 項目 | 本輪確定值 |
|---|---|
| Cloud識別 | `ccarenv_b64_Y2NhcmVudl9kMDg5NTNmYjExNjQ4MTkxYmQ3M2E1OGE0MDBiYzc1Yw`，與M-PORT1相同，runtime running／connected、revision9 |
| 工程目錄 | `/workspace/Twstockai`，唯一可見worktree |
| 正式開發分支 | `blue1998-glitch/Twstockai` → `dev/m1-v018-chart-annotations` |
| 開始本地及遠端 | `8eb817b60ac6393820f58435ecb1b99881d745ac` |
| 私人FM3根 | `/workspace/twstockai-local-data/fm3_20261101/runtime`，目前可讀 |
| 唯一最新主檔 | 根 `CONTINUE_IN_WORK_MODE.md` 最上方；`AGENTS.md`最上方放相同治理規則與主檔指向 |
| 唯一工程寫入者 | 此既有M-PORT1 Codex；不是另一個相同名稱的Codex |

[實際runtime核對](runtime-verification.json) · [歷史整合證據](integration-evidence.json) · [定向驗收](verification.json) · [7方法log](tests.log) · [機器規則](policy.json) · [固定GitHub讀回](GITHUB_READBACK.md)

## 成果已合併與不可知部分

原0.3快照`34b5dfa2`、原修復`4339a146`、原Cloud封存`65b03998`、補充封存`9d48b8d0`、整合結清`4094f130`、進度核對`36b9e277`、PORT1工程`26a69667`均是本輪起點祖先；COMP1／OBS1／UX1等後續完整保留。**兩方已提交的GitHub工程與歷史交付已統一在此分支，不代表兩個Cloud共享未提交檔案。** 本輪不需要再合併產品原碼。

重用原preservation／closure固定SHA讀回與10/30進度核對，確認29份ZIP及兩份manifest仍是相同Git blob；不重新下載、解壓或逐檔重驗歷史890檔。6份衝突歷史檔仍只封存，不覆蓋現在版本。舊環境880原未追蹤檔名與目前保留名單相同，10份歷史診斷已tracked；未把相同檔名當成內容未變證明。沒有發現需新整合的獨有程式；本輪未重新雜湊880檔。

**另一個Cloud沒有附加給此任務，未進入、未搜尋、未清理；其中後來未提交的獨有資料狀態UNKNOWN。** 不能從歷史「已交付清單為空」推定未來或其他環境沒有新檔，也不能宣告全部隱藏備份不存在。若日後取得少量真實獨有程式，僅此Codex依固定來源與版本做可逆正常整合；私人行情不入Git。當下沒有此類可證原件，不能憑摘要還原。

## FM3驗收沿用

原M-PORT1完整指紋清單在Git外；本輪核清單ID、來源可讀性及19,596路徑的集合／size／mtime／inode／device未變，沿用原1,986終態／原件、1,469結果／研究圖驗收，不重讀約19GiB做全量SHA。不是僅看同名路徑或GitHub摘要。這種metadata核對不是抵抗惡意保留mtime竄改的重新內容審計。

目前真實FM3仍未建立獨立備份；重啟／跨環境復原／永久磁碟未知。舊COMP1等在另一檔案系統讀不到FM3是其歷史事實，不能覆寫，也不能再套成本環境資料消失。若未來環境ID不同或缺根，先停受影響工程並標本環境不可用，不做假根、重抓、複製19GiB或破壞性清理。

## 每輪強制接續流程

1. 總監只派到**此既有M-PORT1對話**；不得另開Codex、代理、競爭分支或工程寫入者。唯一主檔為根CONTINUE最新節，不以舊ZIP／舊HEAD開工。
2. 在本對話即時呼叫 `cloud_environment.environment_status`，確認observations_current與running及policy中的精確ID；不能拿上輪回覆或使用者輸入字串當新身分驗證。這個工具由Codex執行，不要求使用者操作手機終端。
3. 執行下列唯讀gate，核正式origin／分支、祖先、本地與遠端頭、原FM3清單／檔案系統、daily／writer鎖、工程鎖及Git index鎖。不同環境、缺原件、來源改動、遠端前進或busy一律停止寫入；遠端前進先讀新增交接，安全接續後再核，不reset／force。
4. 執行有授權的本機工程程式時以`--run`持有同一工程鎖直到程式結束。其他直接編輯也必須遵守同一入口、鎖與單一寫入政策。不得在鎖忙時殺舊程序／刪鎖或啟另一工作。此鎖與源daily鎖分開，無須修改原FM3鎖。
5. 保存前再核遠端；正常commit／push指定分支、固定SHA逐檔原bytes讀回、收據另存。新任務只做授權里程碑，不自啟新研究、介面、資料補建或部署。

```bash
python3 codex/unified_workspace.py --environment-id <本次runtime工具實際回傳ID>
python3 codex/unified_workspace.py --environment-id <本次runtime工具實際回傳ID> --run <已授權本機程式及其參數>
```

腳本不呼叫引擎或來源API、不修改Git或FM3。環境ID參數本身不具平台認證效力，必須先核本次工具觀察。工程鎖位於Git外`/workspace/twstockai-local-data/governance/engineering.lock`；POSIX合作式鎖只限制遵守入口的本機程序。**本Codex沒有平台權限關閉其他對話或跨Cloud強制禁止寫入，不能提供不存在的全域互斥保證。** 不合作／不可見的其他寫入者仍不可確認；分工授權、環境gate、同機鎖及保存前遠端核對共同防止誤寫。

## 本輪驗收及停止

7個唯一新治理方法PASS：正確環境／同名目錄錯Cloud拒絕、錯分支／遠端變化、缺根不誤宣告全域遺失、metadata／清單竄改、跨程序單一鎖及釋放、原source鎖拒絕不刪。中間批不累加；沒有跑PORT1、890檔、產品、producer或Android舊驗收。

本輪只改治理工具與文件；核心、行情、策略、資格與舊交付不改，不建立來源0.11、第二套庫、外部主機／VPN／排程。FM3仍Git外，容量不足不拷貝原件。Oracle尚未完成，真實備份／私人持久部署須另授權。此里程碑固定SHA保存後停止；下一步由Work總監唯讀確認本整併結果，後續工程仍只派回此對話。
