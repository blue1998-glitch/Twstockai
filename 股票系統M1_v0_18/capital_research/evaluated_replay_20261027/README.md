# 合成回放完成後，評估會另存；READ不重算

新的RUN入口會依序：保存完整明示請求 → 沿既有數量回放 → 保存並讀回原結果 → 沿既有評估器 → 另存評估與最終連結。每一步保存都確認後才前進；不是把目標股數當成交，也沒有新選股、比例、行情或排名。

## 直接看保存成果

- [完整原帳成功](actual-final/complete/readable.txt)：原資本2230、期末應計淨值2230，成長／回撤0；原帳假想退出費用另列，退出後報酬仍可能為負。沒有新買賣，是驗證保存接線的合成續抱案例。
- [權利未完整而拒算](actual-final/incomplete/readable.txt)：回放本身完成所給輪次，但期末仍有待交股份，評估REFUSED、統計null。
- [資格不合格而停止](actual-final/stopped/readable.txt)：回放在候選閘門停止，評估仍明確拒算，不拼接停止前績效。
- [完整四階段原件](runs-final/complete/)、[測試log](tests-first.log)、[四階段UNKNOWN](test-evidence/storage-unknown.json)、[缺檔／錯配拒讀](test-evidence/read-refusals.json)。
- [契約](CONTRACT.md)、[結果與限制](REPORT.md)。8個唯一方法首次通過，不累加舊測試、三案例、子程序或故障副本。

原帳現金、股份／待交權利、一般reserve100、latest及全部token仍在原回放／評估原件；沒有另一套帳。成長與回撤採原帳應計淨值，不保證當日能清倉；費用口徑沿原評估器，不重扣。

## READ入口

在`股票系統M1_v0_18/`可讀已保存案例，不會重跑：

```bash
python3 -B -m capital_research.evaluated_replay_cli READ \
  --store capital_research/evaluated_replay_20261027/runs-final/complete \
  --id evaluated-complete
```

加`--format json`讀完整保存評估。READ不接受`--input`，不載入回放／評估引擎、寫檔或網路。成功讀出拒算仍是拒算，退出2；只有可評估的保存結果退出0。來源、保存及研究資格分開。

新RUN必須明示新id、store與完整input；API為`evaluated_replay.run_evaluated_replay(root,id,request)`。同id已存在就停止、改用READ，無自動重跑、重試保存或恢復；request/replay/evaluation/result任一保存UNKNOWN都保留現況。不要把案例的舊id拿來RUN。

## 保留的限制

本入口只接完整明示quantity-replay/0.1輸入。舊研究選擇／補選意圖仍沒有直接接成交，沒有增加1/13行情或新的訂單策略。原引擎不支持的期初應付、信用、外部既有活單等仍拒絕；來源認證、完整分叉、多程序exactly-once、自動復原、R2/F、市場績效與樣本外未完成。

最終使用`runs-final/`及`actual-final/`；`runs/complete/`的空request、`actual/`與`build.log`是測試監看fdopen誤判的歷史診斷，發生在回放前，不是成功結果。監看修正後用新保存位置重新驗證，原件／oracle未改。故障與損壞驗證只使用新暫存副本，並非真實斷電。

1101期初cash_claims UNKNOWN、70／2／其中8／合格真實總淨0及全部正式false／主壓力null不變。使用者目前無需操作；一般工程可留Codex，不預設轉Work。
