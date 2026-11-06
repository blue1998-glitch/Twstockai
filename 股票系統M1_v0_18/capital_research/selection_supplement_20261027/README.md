# 看過候選後，沿原結果明示補選0.1

原操作停在「等待選擇」時，現在可以另存一份明示補選，沿同一份已保存generation選候選並核對來源。原等待結果完整留史，不改成已完成，也不補寫原操作的choice；這樣能保留「當時沒有選、後來才補選」的脈絡。

直接看本輪實際結果：

- [一般意圖：新增B1，目標A60／B26／C2](actual/general/readable.txt)
- [全換：仍只是等待交割重評的條件意圖](actual/conditional/readable.txt)
- [沒有列入原候選的數量：拒絕，不改選](actual/unlisted-quantity/readable.txt)
- [八個定向案例索引](summary.json)、[契約](CONTRACT.md)、[精確輸入與預期](input-expected.json)

## 直接READ已保存補選

在`股票系統M1_v0_18`下：

```sh
python3 -B -m capital_research.selection_supplement_cli READ --parent-store capital_research/research_operation_20261027/initial/runs/no-selection --parent-id demo-no-selection --store capital_research/selection_supplement_20261027/runs/general --id supp-general
```

預設文字，`--format json`看完整回覆。READ必須明示父與補選ID，不自動找最新來源或子紀錄。原操作的READ仍會顯示等待選擇；新補選的READ才顯示新意圖，兩者並不矛盾。

## 明示SELECT

純API為`selection_supplement.select_supplement(parent_store,parent_id,child_store,child_id,request)`；另有`read_supplement`。CLI的SELECT使用相同父／child參數加`--input <完整請求JSON>`。可用[example-request.json](example-request.json)檢視本輪明示合成請求，但新增時須給新的明示child ID及保存目錄；已有ID不重選、不覆寫。無需使用者搬檔或提供私人資料。

請求包含原結果／generation完整綁定、明示股數／端點、理由與含時區紀錄時間。不替使用者選數量、比例、來源或勝者。省略／null選擇拒絕，不預設續抱。沿原`choose_saved`保留完整資格閘門；不支援或不合格仍拒絕，等待交割仍條件意圖。

只接受完整可讀且outcome為AWAITING_EXPLICIT_SELECTION的父結果；停止前prefix、非等待操作、錯父result／generation／帳戶／截止／latest／tokens都拒絕。原帳、來源版本與全部歷史綁定不變。新child只保存`--request`、`--choice`、`--result`，沒有generation、帳本或資本副本；原本金1430、現金275.100、reserve100、A60／B25／C2及原權利完整保留。

補選只記錄原2026-01-12截止的合成研究意圖。2026-10-27的明示紀錄時間不把資料變成最新，也不回填available_at／新決策／今日交易資格。多個child是互斥研究意圖，不能把它們加總成可同時執行的資金配置。

## 本輪驗證及保存

八組新定向輸入符合事前預期：一般、條件、未列數量、非等待父、錯父結果、缺歷史token、缺選擇及父子key重疊。先保存CONTRACT、input／expected、原件指紋及source版本，再執行；舊原件、oracle、actual、manifest與log未修改。來源生成及數值／會計／交易回放呼叫全部0。

[6個唯一方法](tests.log)首次通過，不加歷史PASS。fresh SELECT／READ拒絕數值引擎import、生成及網路；SELECT只寫明示child store，READ另禁選擇、來源check、Journal.save與所有寫檔。父原件前後SHA相同；補選READ與原SELECT保存值相同，原完整state、權利、latest及全部tokens保持。

[同child重送／衝突](idempotence.json)不重選、不改寫。[三階段UNKNOWN](fault-actual.json)使用暫存副本，原Journal寫入後注入OSError：立即停止，明示READ只確認已保存前綴或最終結果，不自動續跑。[錯鏈及缺父結果](corruption-actual.json)在暫存副本驗拒絕且不修復。這些是故障注入證據，不是真實斷電、崩潰檔案救援或市場結果。

保存與資格分開：`SAVED_AND_READ_BACK`不等於合格，`UNKNOWN`不等於成功；只有新結果確認讀回才回報完成。遭拒選擇保存拒絕，不繼續來源核對或改選。所有正式flags false，主壓力null。

## 邊界與交接

沒有來源認證、任意造假防護、複雜分叉／子紀錄自動索引、競爭鎖或中斷自動續跑。完整舊資格矩陣、真實斷電／partial／多程序持久性不重跑，沿原Journal界線；正式資格、來源、1101 UNKNOWN／拒算、70／2／其中8／合格真實總淨0及原未支援帳務保持。R2/F、來源0.10／parents、action_resolution0.4與圖形／人工契約不改。

本輪曾在第一個寫入程序建立前遭exec transport斷線；原環境恢復後已實核原路徑／分支／HEAD、工作區乾淨及新目錄不存在，才開始本工程，沒有換工作區或重建原件。無需人工處理。

基線101c1d3744d18ba0837c4839ff8b6e10dc621a9d；原唯一Codex依既有里程碑於原工作區／原分支完成自審、正常commit/push及GitHub固定SHA原件讀回。固定SHA以Git／回覆為準。不預設轉Work；Astra及第一工作區救援原件仍未取得未讀。無新來源、私人文件、bootstrap、producer／舊suite、UI／Android、樣本外、部署／交易／付費／訊息。
