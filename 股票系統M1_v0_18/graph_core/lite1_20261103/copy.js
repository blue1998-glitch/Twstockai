// Display-only vocabulary and metadata summaries. No prices, events or qualification changes.
const LiteCopy=(()=>{
 const risks={'來源中斷':'新舊資料無法連續比較','資料不足':'保存資料還不夠','研究參照':'參照仍待確認','不同參照結果不一':'各參照結果不同','缺少有效參照':'尚無可比較的參照','參照已停止比較':'參照無法繼續比較','缺少今日行情':'缺少這一天的行情','缺少有效收盤':'沒有可用收盤價','今日零成交':'這一天沒有成交','價量資料不合格':'價量資料尚不能使用','歷史來源不足':'歷史資料還不夠','已跌回參照下':'已跌回參照價下方'};
 const events={OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP:'資料中斷，停止比較',CLOSE_CROSS_UP:'上越參照線',CLOSE_ABOVE_RESEARCH_RANGE:'站上研究區間',CLOSE_CROSS_DOWN:'跌破參照線',CLOSE_BELOW_RESEARCH_RANGE:'跌出研究區間',CLOSE_REENTERED_RANGE:'回到研究區間',FAILED_UP_RETURN_IN_RANGE:'上越後回到區間',RETURN_IN_RANGE_AFTER_BREAKDOWN:'下破後回到區間',FAILED_UP_AND_CROSSED_BELOW_RANGE:'上越後跌出區間',FAILED_UP_RETURN_BELOW:'跌回參照線下',RETURN_ABOVE_AFTER_DOWN:'重回參照線上',CLOSE_EQUALS_REFERENCE:'收盤等於參照線',INITIAL_CLOSE_LOCATION:'首次觀察位置'};
 function risk(value){return risks[value]||(/^[A-Z0-9_:/.-]+$/.test(value||'')?'資料狀態待確認':value)||'限制待確認';}
 function key(value){return value==='未定'||value==='未指定'?'尚無可用價位':value==='多個價位'?'多個參照價位':value;}
 function volume(value){return {'量增（較前筆）':'較前筆量增','量減（較前筆）':'較前筆量減','量平（較前筆）':'與前筆相同','量不可比':'成交量暫不能比較','量未知':'成交量資料不足'}[value]||value;}
 function event(value){return events[value]||'其他保存事件';}
 function overview(state){
  const rows=state.stocks,charts=rows.filter(s=>s.preview_series).length,short=rows.filter(s=>s.status==='INSUFFICIENT_HISTORY').length,judge=rows.filter(s=>s.decision.can_judge).length;
  return {total:rows.length,charts,short,withoutChart:rows.length-charts,judgable:judge,
   message:judge?'可看當期參照變化；不同參照可能有不同結果。':'可看保存走勢；當期結構暫不能判定。'};
 }
 function dateNote(selected,latest){return selected<latest?'較早批次｜最新保存至 '+latest:'已保存收盤資料｜非即時';}
 return {risk,key,volume,event,overview,dateNote};
})();
if(typeof module!=='undefined')module.exports=LiteCopy;
