# 0.3結果至既有數量候選：交付報告

開工實核/workspace/Twstockai、dev/m1-v018-chart-annotations，遠端與HEAD均為51e6db4798ab4c3099200f14632a718b49f818a6；tracked／index／untracked皆0。僅原唯一Codex，沿本輪明確任務與功能里程碑授權有限實作、必要驗證、自審及正常保存讀回。

## 新增能力及重用範圍

`quantity_after_retry.generate_after_retry`接已完成review0.3、完整checkpoint0.8、精確前身與當期研究模板；只補輸入轉接，最後直接呼叫原`quantity_candidates.generate`0.2。原core、execution、continuity、quantity_candidates、quantity_replay、allocation、eligibility、fact_lineage、conditional_retry、lifecycle及action_ledger全部不改。

保存原件／完整checkpoint的execution、origin ledger、compact checkpoint、job／clock／orders及已收到的review requests必須一致；原checkpoint驗證繼續核完整decisions／facts／fills／權利與帳。前身綁原件ID、checkpoint ID、execution ID、latest accepted decision/account及全部tokens，不把遭拒decision升成latest。

原`account_at_checkpoint`導出帳戶，原`quantity_replay._quantity_request`綁account_id／CHECKPOINT_EPISODE，歷史token補入當期輸入，再走原resume。新增B固定ADDITIONAL_BATCH與family C，不能用FIRST_ENTRY或原單豁免繞過。cutoff必等原日終且已可知，來源／基底／版本與估值mark對齊原ledger；不手填account、補價或重開本金。完整性metadata與數值候選分開。

只有無活單／應付、原A仍正持股才接。原A必綁原核准raw plan及其原評估提案，且可由原目標與A-zero追溯唯一減持股票；原記錄無法識別角色則明示NOT_IMPLEMENTED，不能依當前最大持股或任意代碼推定。destination同樣綁原C買單股票。這是本輪原範圍保護，不是新策略條件。

## 事前證據與自審修正

先存`CONTRACT.md`、18案完整來源指紋／模板／edits／materialized input ID／expected，及原件與保護source指紋於`intake.json`，再實作。來源全部為庫內已保存0.3原件與new-batch完整checkpoint；實際API輸入由純IO helper確定性載入，沒有複製原件、抓來源或修改舊結果。新增參數均明示合成來源與available_at。

初批18案符合預期後，自審發現原A角色與raw approval仍可被換名。另先凍結兩案於`role-binding-intake.json`並實跑修前：把C當原A、改寫original_approval，皆仍GENERATED。這是本輪新轉接層的缺口，不是原生成器／帳務缺陷。最小修復綁回原job中的完整raw proposal與原accepted decision的保留欄位；原raw proposal包含edge_budget，評估結果未保存該欄位，首修引用錯欄位造成一次定向檢查失敗。actual、source及`diagnostics/role-binding-check-failure.json`完整留史；修正取證位置，未刪或放寬oracle。

修正後兩案明確拒絕；再以本輪最終source對20個定向輸入執行一次，`after-final/summary.json`全符合原預期。初批／修前／首修／中間正確兩案均留史，不混稱最終結果。沒有執行原retry、舊suite或市場回放來重建證據。

## 最終保存actual

| 案例 | 實際結果 |
| --- | --- |
| new-independent-trigger | GENERATED。四個人工明示格目標為A60/B25、A60/B26、A59/B25、A59/B26，C皆2。加原退A／全換端點共6個不同目標：5個當期可行、1個等待交割重評。不選勝者。 |
| old-trigger | 完整列舉6目標，但新增B的3個候選均被NO_NEW_INDEPENDENT_TRIGGER拒絕；續抱及不新增B候選可保留。 |
| unknown-qualification | 完整列舉，新增B候選因NEW_CAPITAL_NOT_QUALIFIED:B拒絕，不能只看新觸發或內層數值繞過資格。 |
| wrong-latest／missing-tokens／false-first-entry | 精確前身不符或偽首次，無候選輸出。 |
| active-order-refused／payable-refused／zero-incumbent-refused | 原入口範圍阻擋，NOT_IMPLEMENTED；這些是明示結構拒絕變體，不是新回放的合格帳務actual，不能拿來宣稱完整活單／應付重播已驗。 |
| stopped-history-refused／compact-checkpoint-refused | 停止前歷史帳或缺origin／execution的精簡checkpoint拒絕。 |
| wrong-cutoff／wrong-basis／wrong-valuation-mark／manual-account-refused | 錯截止、來源基底、估值或手填帳拒絕，不補未知或回填價格。 |
| tampered-token-history | 改寫compact及完整checkpoint的token state，仍與原ledger／execution重建結果不符，拒絕。 |
| search-limit | 明示格數超限，沒有截斷或部分候選冒完整搜尋。 |
| integrity-metadata-control | 只改完整來源metadata，research與正例完全一致；完整input ID不同，不泛稱所有未來行情變更中立。 |
| wrong-incumbent-role／changed-original-approval | 最終明確拒絕，不能賣其他資產冒稱原A，不能改寫原核准提案。 |

原帳現金275.100／reserve100、A60/B25/C2、已交付權利、12個歷史token與兩個REJECTED／ACCEPTED receipts都從同一checkpoint接續。原資本1430與當期估值1425.100各自保存。每個候選都是從同一帳戶出發的互斥替代方案，不得同時花同一筆錢；全換仍是原full_transfer機械端點及其等待交割限制，不稱最佳比例或已成交。

## 必要測試與保存界線

6個本輪唯一unittest方法一次全通過：20案事前oracle／獨立人工四格、原帳／latest／receipt／權利／全部token、公開API輸入不變／決定性、完整外層閘門、原A修前修後證據，以及metadata隔離／不自動選擇。公開API另在禁止檔案IO、網路、子程序、舊retry／replay_sequence及市場simulate的guard下成功；只允許原checkpoint／帳務驗證與既有數量計算。

綁定最終after-final證據後僅補驗1個受影響方法通過，6唯一／7次方法執行，不把20案例、中間批、修前兩案或歷史7／6等PASS累加。首次method source與原assertions保留，只有actual目錄指標改動。首修定向檢查的失敗不是新增unittest方法，但如實保留診斷。

`after-final/`才綁最終source，`views/`只是其保存JSON的文字投影，不再呼叫產生器。`source-versions-final.json`及`self-review.json`核事前來源、保護source、oracle與公開入口純數值；`CHANGE_MANIFEST.json`含本輪相關檔案、不含自身。原工作入口只在既有AGENTS／CONTINUE與capital README加最新狀態，歷史bytes完整保留。

## 未支援及下一步

無活單／應付以外仍須原incumbent角色可識別、當期mark可知、來源／基底相容及原帳驗證通過；這不是任意0.3 wrapper都可繼續。原A無唯一減持記錄的分支、通用來源認證／job→execution因果及完整分叉未驗，不冒稱可全面防止任意造假。多股最適化、期初應付、外部活單完整重播、信用、R2/F、來源更正及自動解除衝突保持未支援。

本輪沒有委託或成交；輸出checkpoint裡的orders／fills是原保存歷史。沒有新增行情／1/13資料，也沒有執行原retry、真實producer、資格重算、九路徑、市場六方案、UI／Android或樣本外。1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0、全部正式false／主壓力null及正式來源／圖形／人工契約保持；Astra與第一工作區救援原件仍未取得未讀。不冒Work獨立驗收。

本輪不需人工操作。下一步可留在Codex：若使用者指定，先唯讀核對這個新generation能否直接重用既有明示選擇／回放入口；已支援部分不重做，原外部checkpoint resume未支援則保持，不預設比例或新交易規則。本輪不另啟該工程。
