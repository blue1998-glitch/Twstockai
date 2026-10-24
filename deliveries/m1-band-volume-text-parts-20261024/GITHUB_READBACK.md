# 無損文字分片固定交付：GitHub原bytes回讀

固定交付提交：`6d35b7f0e8aefa8d28f1640d0619b28754c4024f`；parent `bd6ed6a984254295eae4c13c5973ef28a7b7c29b`，指定分支dev/m1-v018-chart-annotations。原固定工程ec51f617bf51b1ae77099efc4ecd8099d940996d及全部祖先保留，本輪沒有新產品版本、來源0.11或catalog。

於2026-10-24T09:07:08.053017+00:00完成**23個新增交付檔**固定SHA GitHub raw逐檔實際GET，全部HTTP200、完整bytes／長度／SHA與Git blob一致；含16個UTF-8文字片段、manifest、封裝核驗、原檔觀察／保留證據、README／Work交接及僅標準庫切片原碼。逐檔URL、要求／完成時點及SHA見[GITHUB_READBACK.json](GITHUB_READBACK.json)。未請求原大檔、原blob失敗入口、舊ZIP、PNG或其他舊來源。

- [固定交付入口](https://github.com/blue1998-glitch/Twstockai/blob/6d35b7f0e8aefa8d28f1640d0619b28754c4024f/deliveries/m1-band-volume-text-parts-20261024/README.md)
- [固定manifest raw](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/6d35b7f0e8aefa8d28f1640d0619b28754c4024f/deliveries/m1-band-volume-text-parts-20261024/MANIFEST.json)
- [固定第一片 raw](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/6d35b7f0e8aefa8d28f1640d0619b28754c4024f/deliveries/m1-band-volume-text-parts-20261024/parts/band-volume.part-0001-of-0016.txt)；其餘各片依manifest的相對路徑，同一固定提交取得。
- [固定封裝核驗 raw](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/6d35b7f0e8aefa8d28f1640d0619b28754c4024f/deliveries/m1-band-volume-text-parts-20261024/packaging-verification.json)
- [完整下一輪Work唯讀指令](WORK_HANDOFF.md)

**另外以本次實際從GitHub取得的16片重新串接**：每片可嚴格UTF-8解碼且不超262,144 bytes（低於512 KiB），按順序零分隔串接後為4,102,710 bytes，SHA256 `03961ba8e322a4a1d2cfde52eeb4840f39b4540b2ad61fec8e55c27328621384`。完整bytes與固定ec51f617原JSON相同，JSON可解析且完整物件相同；沒有重新生成、排序、排版或增減換行。這是必要封裝／讀回核驗，不是產品或來源語義重測。

原3958個追蹤檔全部bytes不變，包含原band-volume.json、五JSON、P0-3狀態／事件／ID／角色／價位、策略／引擎／庫、Raw null／UNKNOWN、歷史／舊成品／ZIP／PNG與全部警告；四組原untracked inventory保持。main實核仍 `9c5b168c09ba80010c74f03b9c537e8b7474256a`。本輪只在新交付目錄新增檔案，不修改原產品／交接／來源檔。

Work已回報原10圖及五項用途清楚、五JSON／選取／10/16快照已讀；本Codex未重抓這些圖或重跑驗收，也不把上述證據冒完整JSON已被Work讀取。本環境沒有可呼叫的Work專用GitHub connector；**已證GitHub raw小檔原bytes可取得，不冒稱Work工具已取全或完成完整JSON核讀**。下一步只Work取16片、串接解析後結清本次Work未取得／未讀項。若其工具仍受阻，需列實際片號／路徑／錯誤，不造匹配結果，不要求使用者手機搬檔、終端或架伺服器。

沒有bootstrap／產品工程／32 Python／88 Chromium／數值producer／指標／每日淨帳／六方案／獲利驗證。Android NOT_TESTED_NEW_BUILD、file://未重試。來源0.10全部parent、B88 RESEARCH_CANDIDATE／formal_price_bounds=null、全部來源／個人權利缺口、Raw／五年Adjusted／歷史公布／主檔／SQLite未知保持；不新增策略門檻或密集量峰算法。execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。沒有重試／繞過受拒入口、公開私人原件或補零／行情／前價／估值，無部署、付費、交易、訊息或子代理。

本MD／JSON在固定交付後另行正常提交，兩份收據的固定bytes讀回與最新已核SHA在最後回覆另列，避免自指。
