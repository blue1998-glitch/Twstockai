# 研究選擇紀錄：純READ文字摘要0.1

已保存的選擇紀錄現在可直接讀成文字；不必看整份JSON，也不會重新選候選或啟動回放。這是合成研究意圖，不是委託或成交。

直接閱讀本次實際CLI輸出：

- [一般意圖：目標A60／B26／C2](actual/grid-intent/readable.txt)
- [條件意圖：等待交割後重評](actual/conditional-intent/readable.txt)
- [舊觸發遭拒：沒有選中目標](actual/rejected-old-trigger/readable.txt)

## 使用

在`股票系統M1_v0_18`下執行：

```sh
python3 -B -m capital_research.research_choice_cli READ --store capital_research/research_choice_20261027/journal --id grid-intent --format text
```

省略`--format`仍輸出原JSON；明示`--format json`亦可。原退出碼保持：一般／條件意圖0、遭拒紀錄2。遭拒紀錄仍能正常顯示理由，不把它誤記為新批准。SELECT只接受JSON格式；本輪沒有新增選擇、儲存、委託或回放入口。

純函式為`research_choice_view.render_text(saved_choice)`。CLI沿未改的`read_choice`／Journal讀取與`validate_record`校驗，渲染只投影保存內容，不重算、不找新版、不修復檔案。顯示來源／帳戶／checkpoint／latest指紋、截止、原決策與紀錄時間、歷史與當期reviewed token數；完整token ID仍在原JSON，不改成已消耗token。缺少綁定的拒絕紀錄顯示UNKNOWN，不補零。

## 驗證與證據

先保存[契約](CONTRACT.md)、[三份原件引用與預期](input-expected.json)、[入口拒絕輸入及預期](negative-input-expected.json)及來源指紋，再產生新actual；原件／oracle不改。

- 三份原件的文字與預設JSON實際輸出在`actual/`；預設JSON逐字相容舊READ receipt，原件bytes保持。
- 六項入口拒絕診斷在[negative-actual.json](negative-actual.json)：錯Journal ID、choice內容竄改、未知choice schema、錯envelope schema、缺檔及SELECT要求text。錯誤不輸出半份文字、不寫檔或fallback。
- CLI驗證在fresh process阻擋數值引擎import、choose_saved／select_and_save／Journal.save呼叫、任何寫檔／mkdir／remove／rename、網路與子程序；六項拒絕診斷的暫存輸入前後指紋亦相同。
- 本輪[4個唯一測試方法](tests.log)首次通過，沒有補跑或累加歷史7方法；另測純渲染無IO且完整輸入不變、UNKNOWN綁定、舊SELECT預設／明示JSON呼叫與輸出相容。舊SELECT相容使用保存receipt及受控mock，不冒新數值RUN。

## 限制與交付狀態

目標不是實際持股或成交。紀錄只有候選快照及來源綁定，沒有完整帳本，不能補出現金、reserve、權利變化或新成交；等待交割只記條件意圖，仍須另有當期重評。條件代碼按原件顯示，不發明門檻、比例、訊號或結論。

來源指紋只證內容一致性，不認證來源真偽；紀錄時間不回填歷史可知時間。READ不再次取得完整generation或重新證明原數值。Journal原持久性／單機界線保持，舊schema不遷移。

基線521e0a168c0793859387dc1a0a378788d109d512；依既有功能里程碑由原唯一Codex於原工作區／分支自審、正常commit/push及GitHub固定SHA讀回。固定SHA以Git／回覆為準，沒有人工操作需求、不預設轉Work逐輪驗收。

1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0、正式false／主壓力null及原來源／圖形／帳務限制不變。Astra與第一工作區救援原件仍未取得未讀。沒有舊suite、producer、新行情／來源、私人文件、bootstrap、UI／Android、樣本外或部署交易。R2/F、來源認證、完整分叉及原未支援帳務不擴張。
