  function activeBoxes(){return data.draft_boxes.filter(b=>data.comparison_modes[state.boxMode].includes(b.id));}
  function boxColor(b){return b.id==='A'?'var(--viz-series-1)':'var(--viz-series-2)';}
  function paintBoxes(){
    const boxes=activeBoxes(),step=(width-left-right)/state.count;
    const index=date=>bars.findIndex(b=>b.date===date);
    for(const [svg,y,h,volume,clip] of [[px,py,priceH,false,'box-price-clip'],[vx,vy,volumeH,true,'box-volume-clip']]){
      svg.selectAll('defs').data([0]).join('defs').selectAll('clipPath').data([clip]).join('clipPath').attr('id',clip)
        .selectAll('rect').data([0]).join('rect').attr('x',left).attr('y',top).attr('width',width-left-right).attr('height',h-top-bottom);
      const g=svg.selectAll('g.box-background').data([0]).join('g').attr('class','box-background').attr('clip-path',`url(#${clip})`);
      g.lower();
      g.selectAll('rect.box-shade').data(boxes,b=>b.id).join('rect').attr('class','box-shade').attr('data-box',b=>b.id)
        .attr('x',b=>x(index(b.start))-.46*step).attr('width',b=>Math.max(.5,(index(b.end)-index(b.start)+.92)*step))
        .attr('y',b=>volume?y(+b.max_volume_shares/1e6):y(+b.high))
        .attr('height',b=>volume?y(0)-y(+b.max_volume_shares/1e6):y(+b.low)-y(+b.high))
        .attr('fill',boxColor).attr('fill-opacity',.18).attr('stroke','none');
    }
    const visible=boxes.filter(b=>index(b.end)>=state.first&&index(b.start)<state.first+state.count);
    px.selectAll('text.box-name').data(visible,b=>b.id).join('text').attr('class','box-name')
      .attr('x',b=>Math.max(left+6,Math.min(width-right-30,x(index(b.start))+5)))
      .attr('y',b=>Math.max(top+14,py(+b.high)+14)).text(b=>b.id);
    root.querySelector('.box-summary').textContent=boxes.map(b=>`${b.id} ${b.start.slice(5)}～${b.end.slice(5)}｜${b.low}～${b.high}`).join('　');
    root.dataset.boxMode=state.boxMode;
  }
  function paintBoxEvidence(){
    const points=activeBoxes().flatMap(b=>[['high',b.high_dates,b.high],['low',b.low_dates,b.low]].flatMap(([kind,dates,value])=>dates.map(date=>({id:b.id,kind,date,value:+value,i:bars.findIndex(r=>r.date===date)}))))
      .filter(p=>p.i>=state.first&&p.i<state.first+state.count&&p.value>=py.domain()[0]&&p.value<=py.domain()[1]);
    px.selectAll('circle.box-extreme').data(points,p=>p.id+p.kind+p.date).join('circle').attr('class','box-extreme')
      .attr('cx',p=>x(p.i)).attr('cy',p=>py(p.value)).attr('r',3).attr('fill',boxColor).attr('pointer-events','none');
    const events=data.price_comparisons.map(e=>({...e,i:bars.findIndex(b=>b.date===e.date)})).filter(e=>e.i>=state.first&&e.i<state.first+state.count&&+e.close>=py.domain()[0]&&+e.close<=py.domain()[1]);
    px.selectAll('text.price-comparison').data(events,e=>e.id).join('text').attr('class','price-comparison')
      .attr('x',e=>Math.max(left+5,Math.min(width-right-16,x(e.i)+5))).attr('y',e=>Math.max(top+14,py(+e.close)-9)).text(e=>e.id);
  }
  root.querySelectorAll('[data-box-mode]').forEach(button=>button.addEventListener('click',()=>{
    state.boxMode=button.dataset.boxMode;
    root.querySelectorAll('[data-box-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    draw(false);
  }));
