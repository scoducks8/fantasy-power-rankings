/* GPU Express: an 8-bit parody side-scroller. Data comes from window.JGAME. */
(function(){
  var D = window.JGAME || {teams: [], week: 0};
  var cv = document.getElementById('jg');
  if (!cv) return;
  var ctx = cv.getContext('2d');
  var ov = document.getElementById('jgov');
  var NARROW = (cv.parentElement.clientWidth||800) < 600;
  var W = NARROW ? 208 : 320, H = 180, S = 3, GROUND = 156, SEG = 400;
  cv.width = W * S; cv.height = H * S;
  cv.parentElement.style.aspectRatio = W + '/' + H;
  ctx.imageSmoothingEnabled = false;
  var FONT = '"Press Start 2P", monospace', SMALL = 'Silkscreen, monospace';
  var GREEN = '#76b900';

  // ---------- sprites ----------
  var PAL = {n:'#4a2412',d:'#d0213f',k:'#121212',K:'#5e5e5e',h:'#5c5c5c',s:'#e3b48c',S:'#bf8a62',w:'#9fd3ff',t:'#202020',j:'#2d3650',b:'#050505',
    f:'#6b5233',F:'#2e2216',c:'#b38b52',C:'#8a6a3a',H:'#8d8d8d',u:'#3b4352',W:'#f4f4f4',r:'#d63a3a',p:'#c79a5a',
    G:GREEN,m:'#545454',M:'#a5a5a5',y:'#e2b33c',g:'#2a2a2a'};
  function mk(rows){
    var h = rows.length, w = rows[0].length, c = document.createElement('canvas');
    c.width = w * S; c.height = h * S;
    var g = c.getContext('2d');
    for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) {
      var ch = rows[y].charAt(x);
      if (ch !== '.' && PAL[ch]) { g.fillStyle = PAL[ch]; g.fillRect(x * S, y * S, S, S); }
    }
    var f = document.createElement('canvas'); f.width = c.width; f.height = c.height;
    var fg = f.getContext('2d'); fg.translate(c.width, 0); fg.scale(-1, 1); fg.drawImage(c, 0, 0);
    return {c: c, f: f, w: w, h: h};
  }
  var JTOP = ['...kkkkkk...','..kkkkkkkk..','..khsssssk..','..sggwsgws..','..sssssssS..','...ssSSss...',
    '..KkkttkkK..','.KkkkttkkkK.','.KkKkttkKkK.','.sKkkttkkKs.','..kkkkkkkk..','..jjjjjjjj..'];
  var J1 = mk(JTOP.concat(['..jjj..jjj..','..jjj..jjj..','..jj....jj..','.bbb....bbb.']));
  var J2 = mk(JTOP.concat(['..jjj.jjj...','...jjjjj....','...jj.jj....','..bbb.bbb...']));
  var J3 = mk(JTOP.concat(['.jjj....jjj.','jjj......jjj','bb........bb','............']));
  var SPY1 = mk(['............','...ffffff...','...FFFFFF...','.ffffffffff.','...ssssss...','...kkkkkk...','...ssssss...',
    '..cCccccCc..','.ccCccccCcc.','.ccCccccCcc.','.sccFFFFccs.','..cccccccc..','..cccccccc..','..jj....jj..','..jj....jj..','.bbb....bbb.']);
  var SPY2 = mk(['............','...ffffff...','...FFFFFF...','.ffffffffff.','...ssssss...','...kkkkkk...','...ssssss...',
    '..cCccccCc..','.ccCccccCcc.','.ccCccccCcc.','.sccFFFFccs.','..cccccccc..','..cccccccc..','...jj..jj...','...jjjjj....','..bbb.bbb...']);
  var TRAPTOP = ['....nnnn....','...nnnnnn...','..nnssssnn..','..nskssksn..','..nssssssn..','..nnsrrsnn..','.nnn.ss.nnn.',
    '.nn.dddd.nn.','..sddddddS..','..s.dddd.S..','...dddddd...','...dddddd...','..dddddddd..'];
  var TRAP1 = mk(TRAPTOP.concat(['...ss..ss...','...ss..ss...','...ss..ss...','...ss..ss...','..dd...dd...']));
  var TRAP2 = mk(TRAPTOP.concat(['....s..ss...','...ss.ss....','...ss.ss....','...s..ss....','..dd.dd.....']));
  var HEART = mk(['.d.d.','ddddd','ddddd','.ddd.','..d..']);
  var AUD1 = mk(['............','...HHHHHH...','..HssssssH..','...skkskk...','...ssssss...','....ssss....',
    '..uuWrWuu...','.uuuWrWuuuW.','.uuuWrWuupW.','.uuuurruupW.','.suuuuuuupp.','..uuuuuuu...','..uuu.uuu...','..uuu.uuu...','..uu...uu...','.bbb...bbb..']);
  var AUD2 = mk(['............','...HHHHHH...','..HssssssH..','...skkskk...','...ssssss...','....ssss....',
    '..uuWrWuuWW.','.uuuWrWuuuW.','.uuuWrWuupps','.uuuurruupp.','.suuuuuuu...','..uuuuuuu...','..uuu.uuu...','..uuu.uuu...','..uu...uu...','.bbb...bbb..']);
  var GPU = mk(['GGGGGGGGGGGG','kmmmkkkkmmmk','kmMmkGGkmMmk','kmmmkkkkmmmk','kkkkkkkkkkkk','.yy.yy.yy...']);
  var JACKET = mk(['.kk..kk.','kKkkkkKk','kKkttkKk','kkkttkkk','.kkttkk.','.kkkkkk.']);

  // ---------- helpers ----------
  function rng(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
  function R(x,y,w,h,c){ctx.fillStyle=c;ctx.fillRect(Math.round(x)*S,Math.round(y)*S,Math.round(w)*S,Math.round(h)*S)}
  function spr(s,x,y,flip){ctx.drawImage(flip?s.f:s.c,Math.round(x)*S,Math.round(y)*S)}
  function T(str,x,y,size,col,align,font){
    ctx.font=(size*S)+'px '+(font||FONT);ctx.textAlign=align||'left';ctx.textBaseline='top';
    if(col!=='#111'){ctx.fillStyle='#000';ctx.fillText(str,Math.round(x)*S+S,Math.round(y)*S+S);}
    ctx.fillStyle=col;ctx.fillText(str,Math.round(x)*S,Math.round(y)*S);
  }
  function hit(a,b){return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y}
  function clamp(v,a,b){return v<a?a:v>b?b:v}
  function wrap(n,len){var w=String(n).toUpperCase().split(/\s+/),out=[''];
    w.forEach(function(x){var c=out[out.length-1];if(!c)out[out.length-1]=x;else if((c+' '+x).length<=len)out[out.length-1]=c+' '+x;else out.push(x)});
    if(out.length>2){out=[out[0],out.slice(1).join(' ')]}
    return out.map(function(l){return l.length>len?l.slice(0,len-1)+'.':l})}
  function short(n,len){n=String(n).toUpperCase();return n.length>len?n.slice(0,len-1)+'.':n}

  // ---------- sound ----------
  var AC=null, muted=false;
  try{muted=localStorage.getItem('jg-muted')==='1'}catch(_){}
  function snd(t){
    if(muted)return;
    try{
      AC=AC||new (window.AudioContext||window.webkitAudioContext)();
      var f={jump:[330,660,.11],coin:[988,1480,.07],hit:[220,60,.3],ship:[392,1568,.35],stomp:[180,720,.12],die:[440,55,.6]}[t];
      var o=AC.createOscillator(),g=AC.createGain(),n=AC.currentTime;
      o.type='square';o.frequency.setValueAtTime(f[0],n);o.frequency.exponentialRampToValueAtTime(f[1],n+f[2]);
      g.gain.setValueAtTime(.05,n);g.gain.exponentialRampToValueAtTime(.001,n+f[2]);
      o.connect(g);g.connect(AC.destination);o.start(n);o.stop(n+f[2]+.02);
    }catch(_){}
  }

  // ---------- teams (worst first) ----------
  var teams = D.teams.slice().sort(function(a,b){return b.rank-a.rank});
  var N = teams.length;
  teams.forEach(function(t){ if(t.logo){ t.img=new Image(); t.img.src=t.logo; } });
  var LEVEL = N*SEG + 140;
  var SHOPS = ['#e9a3a3','#9fd8c6','#f2d179','#b3c6ee','#e4b7e0','#f0b47e'];

  // ---------- level ----------
  var L;
  function build(){
    var r = rng((D.week||1)*7919+3);
    L = {solids:[],plats:[],gpus:[],foes:[],shells:[],papers:[],pits:[],fx:[],sky:[],mid:[]};
    for (var s=0;s<N;s++){
      var x0 = s*SEG, hard = s/Math.max(1,N-1);
      var pit = null;
      if (s>0 && (s%2===1 || s>=7)) {
        var pw = 30 + Math.min(14, s*2);
        var px = x0 + 150 + Math.floor(r()*70);
        pit = {x:px,w:pw};
        L.pits.push(pit);
        L.solids.push({x:x0,y:GROUND,w:px-x0,h:60});
        L.solids.push({x:px+pw,y:GROUND,w:x0+SEG-(px+pw)+(s===N-1?140:0),h:60});
        for (var a=0;a<3;a++) L.gpus.push({x:px+pw/2-6+(a-1)*14,y:GROUND-34-(a===1?8:0)});
      } else {
        L.solids.push({x:x0,y:GROUND,w:SEG+(s===N-1?140:0),h:60});
      }
      // racks
      var p1x = x0 + 44 + Math.floor(r()*40);
      if (pit && p1x+52 > pit.x-6 && p1x < pit.x+pit.w+6) p1x = pit.x - 64;
      var p1 = {x:p1x,y:120,w:48,h:8};
      L.plats.push(p1);
      for (var g=0;g<3;g++) L.gpus.push({x:p1.x+6+g*14,y:p1.y-10});
      if (s>=2 && s%2===0) {
        var p2 = {x:p1.x+68,y:94,w:40,h:8};
        L.plats.push(p2);
        for (g=0;g<2;g++) L.gpus.push({x:p2.x+8+g*14,y:p2.y-10});
      }
      // ground gpus
      var gx = x0 + (pit ? (pit.x+pit.w+16) : 210);
      for (g=0;g<3;g++) L.gpus.push({x:gx+g*16,y:GROUND-10});
      if (s===0) for (g=0;g<3;g++) L.gpus.push({x:x0+70+g*16,y:GROUND-10});
      // enemies (better teams are harder)
      var spies = s===0 ? 1 : 1 + Math.floor(hard*2.5);
      for (var i=0;i<spies;i++){
        var sx = x0 + 120 + i*70 + Math.floor(r()*20);
        if (pit && sx+12 > pit.x-4 && sx < pit.x+pit.w+4) sx = pit.x+pit.w+10;
        if (sx > x0+SEG-110) sx = x0+SEG-110-i*10;
        L.foes.push({k:'trap',x:sx,y:GROUND-16,w:10,h:15,vx:(i%2?1:-1)*(.35+hard*.45),min:sx-50,max:sx+50,dead:false,vy:0});
      }
      if (s>=2) {
        var onRack = s%2===0;
        var ax = onRack ? p1.x+18 : x0+SEG-140;
        L.foes.push({k:'aud',x:ax,y:(onRack?p1.y:GROUND)-16,w:10,h:15,vx:0,dead:false,vy:0,
          cd:60+Math.floor(r()*40),every:Math.max(70,130-s*6),face:true});
      }
      var last = s===N-1;
      var sw = last?92:56;
      L.shells.push({x:x0+SEG-sw-14,w:sw,door:x0+SEG-14-sw/2,team:teams[s],idx:s,done:false,last:last,col:SHOPS[s%SHOPS.length]});
    }
    // background
    var bx = 0, rb = rng(99);
    while (bx < LEVEL*0.3+W) { var bw=18+Math.floor(rb()*26),bh=30+Math.floor(rb()*70);L.sky.push({x:bx,w:bw,h:bh,seed:Math.floor(rb()*1e6)});bx+=bw+2+Math.floor(rb()*6); }
    bx = 0;
    while (bx < LEVEL*0.6+W) { var mw=26+Math.floor(rb()*20);L.mid.push({x:bx,w:mw,h:26+Math.floor(rb()*30)});bx+=mw+30+Math.floor(rb()*60); }
  }

  // ---------- state ----------
  var P, K={l:0,r:0,j:0}, state='title', cam=0, frame=0, lives=3, carry=0, shipped=0, score=0, next=0, ck=20, total=0, inView=true, best=0, ticks=0, stomps=0;
  var SB = D.scoreboard || '';
  try{best=+localStorage.getItem('jg-best-'+D.week)||0}catch(_){}
  function reset(full){
    if(full){build();lives=3;carry=0;shipped=0;score=0;next=0;ck=20;total=L.gpus.length;ticks=0;stomps=0;}
    P={x:ck,y:GROUND-40,w:10,h:15,vx:0,vy:0,on:false,face:false,inv:60,coy:0,jHeld:true,anim:0};
    L.papers=[];
    cam=clamp(P.x-W*.38,0,LEVEL-W);
  }
  build(); total=L.gpus.length; reset(false); P.x=40;

  function fx(text,x,y,col){L.fx.push({t:text,x:x,y:y,c:col||'#fff',life:50})}

  function solidAt(x,y){
    var i,b;
    for(i=0;i<L.solids.length;i++){b=L.solids[i];if(x>=b.x&&x<b.x+b.w&&y>=b.y&&y<b.y+b.h)return true}
    for(i=0;i<L.plats.length;i++){b=L.plats[i];if(x>=b.x&&x<b.x+b.w&&y>=b.y&&y<b.y+4)return true}
    return false;
  }

  function hurt(from){
    if(P.inv>0)return;
    lives--;
    var lost=Math.ceil(carry/2);carry-=lost;
    var trap=from&&from.k==='trap';
    fx(trap?('HONEYTRAP'+(lost?' -'+lost:'')):lost?('SEIZED -'+lost):'OUCH',P.x-14,P.y-10,trap?'#ff8fb1':'#ff6b5b');
    P.inv=100;P.vy=-3;P.vx=(from&&from.x>P.x)?-2:2;
    snd('hit');
    if(lives<=0)over();
  }
  function fall(){
    lives--;carry=0;snd('die');
    if(lives<=0){over();return}
    fx('EXPORT CONTROLLED',ck-10,GROUND-50,'#ff6b5b');
    reset(false);
  }

  function step(){
    frame++;ticks++;
    var ax=(K.r?1:0)-(K.l?1:0);
    if(ax){P.vx+=ax*.22;P.face=ax<0}else{P.vx*=.75;if(Math.abs(P.vx)<.05)P.vx=0}
    P.vx=clamp(P.vx,-1.9,1.9);
    if(K.j&&!P.jHeld&&(P.on||P.coy>0)){P.vy=-5.3;P.on=false;P.coy=0;snd('jump')}
    if(!K.j&&P.vy<-2)P.vy=-2;
    P.jHeld=!!K.j;
    P.vy=Math.min(P.vy+.28,6);
    P.x+=P.vx;
    var i,b;
    for(i=0;i<L.solids.length;i++){b=L.solids[i];if(hit(P,b)){if(P.vx>0)P.x=b.x-P.w;else if(P.vx<0)P.x=b.x+b.w;P.vx=0}}
    P.x=clamp(P.x,0,LEVEL-P.w);
    var prevB=P.y+P.h;
    P.y+=P.vy;P.on=false;
    for(i=0;i<L.solids.length;i++){b=L.solids[i];if(hit(P,b)){if(P.vy>0){P.y=b.y-P.h;P.on=true}else P.y=b.y+b.h;P.vy=0}}
    if(P.vy>=0)for(i=0;i<L.plats.length;i++){b=L.plats[i];
      if(prevB<=b.y+.01&&P.y+P.h>=b.y&&P.x+P.w>b.x&&P.x<b.x+b.w){P.y=b.y-P.h;P.vy=0;P.on=true}}
    P.coy=P.on?6:P.coy-1;
    if(P.inv>0)P.inv--;
    if(Math.abs(P.vx)>.3&&P.on)P.anim++;
    if(P.y>H+10){fall();return}

    // gpus
    for(i=0;i<L.gpus.length;i++){var g=L.gpus[i];
      if(!g.got&&hit(P,{x:g.x,y:g.y,w:12,h:6})){g.got=true;carry++;snd('coin');fx('+1',g.x,g.y-6,GREEN)}}
    // foes
    for(i=0;i<L.foes.length;i++){var f=L.foes[i];
      if(f.dead){f.vy+=.3;f.y+=f.vy;continue}
      if(Math.abs(f.x-P.x)>260)continue;
      if(f.k==='trap'){
        f.x+=f.vx;
        var front=f.vx>0?f.x+f.w+1:f.x-1;
        if(!solidAt(front,f.y+f.h+2)||f.x<f.min||f.x>f.max)f.vx=-f.vx;
      }else{
        f.face=P.x<f.x;
        if(--f.cd<=0&&Math.abs(P.x-f.x)<180&&Math.abs(P.y-f.y)<70){
          L.papers.push({x:f.x+(f.face?-4:10),y:f.y+5,w:5,h:5,vx:f.face?-1.5:1.5,life:220});f.cd=f.every;f.throwT=14;
        }
        if(f.throwT)f.throwT--;
      }
      if(hit(P,f)){
        if(f.k==='aud'&&P.vy>.5&&prevB<=f.y+6){
          f.dead=true;f.vy=-2.5;P.vy=-4;score+=200;stomps++;snd('stomp');
          fx('AUDIT CLOSED',f.x-14,f.y-10,'#ffd84a');
        }else hurt(f);
      }
    }
    for(i=L.papers.length-1;i>=0;i--){var p=L.papers[i];p.x+=p.vx;p.life--;
      if(hit(P,p)){L.papers.splice(i,1);hurt(p);continue}
      if(p.life<=0)L.papers.splice(i,1)}
    // shell companies
    var sh=L.shells[next];
    if(sh&&P.x+P.w/2>=sh.door){
      sh.done=true;var got=carry;shipped+=carry;score+=carry*100;carry=0;ck=sh.door+18;next++;
      snd('ship');card(sh,got);
    }
    cam+=(clamp(P.x-W*.38,0,LEVEL-W)-cam)*.15;
    for(i=L.fx.length-1;i>=0;i--){L.fx[i].y-=.4;if(--L.fx[i].life<=0)L.fx.splice(i,1)}
  }

  // ---------- drawing ----------
  function drawBG(){
    var bands=['#04060a','#060a10','#081010','#0a1510','#0c1a10'];
    for(var i=0;i<bands.length;i++)R(0,i*30,W,30,bands[i]);
    R(0,150,W,30,'#0c1a10');
    for(i=0;i<40;i++){var sx=((i*73)%W - cam*.05%W + W)%W, sy=(i*37)%90;R(sx,sy,1,1,i%5?'#3b4a3b':'#cfe8a8')}
    // Singapore skyline near the end
    var sgx = (LEVEL-W)*.3 - cam*.3 + W*.55;
    if (sgx > -120 && sgx < W+40) {
      R(sgx,40,14,110,'#0d1712');R(sgx+22,40,14,110,'#0d1712');R(sgx+44,40,14,110,'#0d1712');
      R(sgx-8,34,74,6,'#11211a');R(sgx-10,36,4,2,'#11211a');
      for(var w=0;w<12;w++){R(sgx+3,48+w*8,8,2,'#2c4a22');R(sgx+25,48+w*8,8,2,'#2c4a22');R(sgx+47,48+w*8,8,2,'#2c4a22')}
    }
    for(i=0;i<L.sky.length;i++){var b=L.sky[i],x=b.x-cam*.3;if(x+b.w<0||x>W)continue;
      R(x,150-b.h,b.w,b.h,'#0b130e');
      var sd=b.seed;for(var yy=150-b.h+4;yy<146;yy+=6)for(var xx=x+3;xx<x+b.w-3;xx+=5){sd=(sd*9301+49297)%233280;if(sd%7===0)R(xx,yy,2,2,sd%3?'#2f5a1c':'#6e6a2c')}}
    for(i=0;i<L.mid.length;i++){var m=L.mid[i],mx=m.x-cam*.6;if(mx+m.w<0||mx>W)continue;
      R(mx,GROUND-m.h,m.w,m.h,'#141c18');R(mx,GROUND-m.h,m.w,2,'#1f2b24');
      for(var ly=GROUND-m.h+6;ly<GROUND-4;ly+=6){R(mx+4,ly,2,2,((frame>>4)+ly+i)%5?'#2a3a2f':GREEN);R(mx+m.w-8,ly,4,1,'#2a3a2f')}}
  }
  function drawWorld(){
    var i,b,x;
    for(i=0;i<L.solids.length;i++){b=L.solids[i];x=b.x-cam;if(x+b.w<0||x>W)continue;
      R(x,b.y,b.w,b.h,'#161c17');R(x,b.y,b.w,2,GREEN);R(x,b.y+2,b.w,1,'#3d5f05');
      for(var tx=Math.ceil(b.x/16)*16;tx<b.x+b.w;tx+=16)R(tx-cam,b.y+3,1,21,'#0d110e');
      R(x,b.y+12,b.w,1,'#0d110e')}
    for(i=0;i<L.pits.length;i++){var p=L.pits[i];x=p.x-cam;if(x+p.w<-40||x>W+40)continue;
      R(x-26,GROUND-22,2,22,'#777');R(x-34,GROUND-30,18,10,'#e8c33a');R(x-33,GROUND-29,16,8,'#1b1b1b');
      T('EXPORT',x-33,GROUND-29,3,'#e8c33a','left',SMALL);T('CTRL',x-31,GROUND-25,3,'#e8c33a','left',SMALL)}
    for(i=0;i<L.plats.length;i++){b=L.plats[i];x=b.x-cam;if(x+b.w<0||x>W)continue;
      R(x,b.y,b.w,b.h,'#2b313a');R(x,b.y,b.w,1,'#5a6474');R(x,b.y+b.h-1,b.w,1,'#14181d');
      for(var lx=x+3;lx<x+b.w-3;lx+=5)R(lx,b.y+3,2,2,((frame>>3)+lx)%4?'#3a4350':GREEN)}
    if(cam<160){var sx0=6-cam;R(sx0+20,GROUND-34,2,34,'#888');R(sx0,GROUND-46,64,14,'#1f5a2a');R(sx0,GROUND-46,64,1,'#fff6');
      T('TO SINGAPORE >',sx0+32,GROUND-44,3,'#fff','center',SMALL);T(N+' SHELL COMPANIES',sx0+32,GROUND-39,3,'#ffd84a','center',SMALL)}
    for(i=0;i<L.shells.length;i++)drawShell(L.shells[i]);
    var bob=Math.round(Math.sin(frame/10)*1.5);
    for(i=0;i<L.gpus.length;i++){var g=L.gpus[i];if(g.got)continue;x=g.x-cam;if(x<-14||x>W)continue;spr(GPU,x,g.y+bob)}
    for(i=0;i<L.foes.length;i++){var f=L.foes[i];x=f.x-cam;if(x<-16||x>W+4||f.y>H)continue;
      var sp=f.k==='trap'?((frame>>4)%2?TRAP1:TRAP2):(f.throwT?AUD2:AUD1);
      if(f.dead){ctx.save();ctx.globalAlpha=.6;spr(sp,x-1,f.y-1,f.face);ctx.restore();continue}
      spr(sp,x-1,f.y-(f.k==='trap'?3:1),f.k==='trap'?f.vx<0:f.face);
      if(f.k==='trap'&&Math.abs(f.x-P.x)<130)spr(HEART,x+3,f.y-10-((frame>>4)%2));
    }
    for(i=0;i<L.papers.length;i++){var pp=L.papers[i];x=pp.x-cam;R(x,pp.y,5,5,'#f4f4f4');R(x+1,pp.y+1,3,1,'#999');R(x+1,pp.y+3,3,1,'#999')}
    if(!(P.inv>0&&(frame>>2)%2)){
      var js=!P.on?J3:(Math.abs(P.vx)>.3?((P.anim>>3)%2?J1:J2):J1);
      spr(js,P.x-1-cam,P.y-1,P.face);
    }
    for(i=0;i<L.fx.length;i++){var e=L.fx[i];T(e.t,e.x-cam,e.y,5,e.c,'left',SMALL)}
  }
  function drawShell(sh){
    var x=sh.x-cam;if(x+sh.w<-30||x>W+30)return;
    var t=sh.team;
    if(sh.last){
      var top=GROUND-104;
      for(var k=0;k<3;k++){R(x+6+k*30,top+10,20,104-10,'#cfd6dc');R(x+6+k*30,top+10,2,94,'#eef2f4');
        for(var wy=top+16;wy<GROUND-6;wy+=6)R(x+9+k*30,wy,14,2,(wy+k*3+(frame>>4))%5?'#7e8d99':'#ffe27a')}
      R(x-6,top,sh.w+12,8,'#e9eef1');R(x-8,top+2,4,4,'#e9eef1');R(x+sh.w+4,top+2,6,3,'#76b900');
      R(x+10,top-18,sh.w-20,16,'#0b0b0b');R(x+10,top-18,sh.w-20,1,GREEN);
      T('#1 '+short(t.name,12),x+sh.w/2,top-15,4,'#ffd84a','center',SMALL);
      T('HOLDINGS PTE. LTD. · SG',x+sh.w/2,top-9,3,GREEN,'center',SMALL);
      R(x+sh.w/2-24,top-29,48,10,'#ffd84a');T('SHELL CO. HQ',x+sh.w/2,top-27,4,'#111','center',SMALL);
      if(t.img&&t.img.complete&&t.img.naturalWidth)ctx.drawImage(t.img,Math.round(x+sh.w/2-9)*S,(GROUND-62)*S,18*S,18*S);
      R(x+sh.w/2-9,GROUND-22,18,22,'#111');
    } else {
      var y=GROUND-58;
      R(x,y,sh.w,58,sh.col);R(x,y,sh.w,2,'#fff8');
      R(x-3,y-3,sh.w+6,5,'#7a4b33');
      R(x-3,y-15,sh.w+6,11,sh.done?'#8a7a3a':'#ffd84a');R(x-3,y-15,sh.w+6,1,'#fff3');
      T('#'+t.rank+' SHELL CO.',x+sh.w/2,y-13,4,'#111','center',SMALL);
      for(var sx=0;sx<3;sx++){if(sx===1)continue;R(x+5+sx*17,y+24,12,10,'#1f2a28');R(x+6+sx*17,y+25,10,8,'#141c1b');T('EMPTY',x+11+sx*17,y+27,2,'#5a6b67','center',SMALL)}
      for(var mb=0;mb<6;mb++)R(x+sh.w/2+9+(mb%2)*5,GROUND-18+Math.floor(mb/2)*5,4,4,'#b8913a');
      R(x+2,y+4,sh.w-4,18,'#0b0b0b');
      var ln=wrap(t.name,15);
      for(var q=0;q<ln.length;q++)T(ln[q],x+sh.w/2,y+5+q*5,3,'#fff','center',SMALL);
      T('PTE. LTD. · SINGAPORE',x+sh.w/2,y+16,3,GREEN,'center',SMALL);
      R(x+sh.w/2-7,GROUND-20,14,20,'#1a1a1a');R(x+sh.w/2-7,GROUND-20,14,1,'#555');
      if(t.img&&t.img.complete&&t.img.naturalWidth)ctx.drawImage(t.img,Math.round(x+sh.w/2-6)*S,(GROUND-37)*S,12*S,12*S);
      R(x+sh.w+3,y-26,1,84,'#999');R(x+sh.w+4,y-26,11,4,'#e2232a');R(x+sh.w+4,y-22,11,4,'#fff');R(x+sh.w+5,y-25,2,2,'#fff');
    }
    if(!sh.done&&L.shells[next]===sh&&(frame>>4)%2)T('V',x+sh.w/2,GROUND-(sh.last?32:30),5,GREEN,'center',SMALL);
  }
  function drawHUD(){
    var sh=L.shells[next];
    if(NARROW){
      R(0,0,W,22,'rgba(0,0,0,.72)');R(0,22,W,1,GREEN);
      for(var i=0;i<lives;i++)spr(JACKET,3+i*10,3);
      T('GPU '+carry,38,3,5,GREEN,'left',SMALL);
      T('SHIP '+shipped,80,3,5,'#fff','left',SMALL);
      T(clock(),W-3,13,4,'#cfd8cf','right',SMALL);T(String(score),W-3,3,5,'#ffd84a','right',SMALL);
      if(sh)T('NEXT #'+sh.team.rank+' '+short(sh.team.name,18),3,13,4,'#cfd8cf','left',SMALL);
      return;
    }
    R(0,0,W,14,'rgba(0,0,0,.72)');R(0,14,W,1,GREEN);
    for(var i=0;i<lives;i++)spr(JACKET,4+i*10,4);
    T('GPU '+carry,40,4,5,GREEN,'left',SMALL);
    T('SHIPPED '+shipped,82,4,5,'#fff','left',SMALL);
    T(String(score),160,4,5,'#ffd84a','left',SMALL);T(clock(),205,4,5,'#cfd8cf','left',SMALL);
    if(sh)T('NEXT #'+sh.team.rank+' '+short(sh.team.name,11),W-4,4,5,'#cfd8cf','right',SMALL);
  }
  function draw(){
    ctx.clearRect(0,0,cv.width,cv.height);
    drawBG();drawWorld();
    if(state!=='title')drawHUD();
    if(state==='title'){R(0,0,W,H,'rgba(0,0,0,.35)')}
  }

  // ---------- overlays ----------
  function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e}
  function btn(label,fn,cls){var b=el('button','jbtn'+(cls?' '+cls:''),label);b.type='button';b.addEventListener('click',function(ev){ev.preventDefault();fn()});return b}
  var primary=null;
  function show(nodes,pri){ov.innerHTML='';nodes.forEach(function(n){ov.appendChild(n)});ov.hidden=false;primary=pri||null;
    var b=ov.querySelector('.jbtn');if(b&&inView)try{b.focus({preventScroll:true})}catch(_){}}
  function hide(){ov.hidden=true;ov.innerHTML='';primary=null}
  function clock(){var t=Math.floor(ticks/60);return Math.floor(t/60)+':'+('0'+t%60).slice(-2)}
  function sbGet(cb){if(!SB||!window.fetch)return cb(null);
    fetch(SB+(SB.indexOf('?')<0?'?':'&')+'week='+encodeURIComponent(D.week)).then(function(r){return r.json()}).then(function(d){cb(d&&d.top||[])},function(){cb(null)})}
  function sbPost(o,cb){if(!SB||!window.fetch)return cb(null);
    fetch(SB,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(o)})
      .then(function(r){return r.json()}).then(function(d){cb(d&&d.ok?(d.top||[]):null)},function(){cb(null)})}
  function boardInto(box,list,me,n){
    box.innerHTML='';
    if(list===null){box.appendChild(el('p','jsmall',SB?'SCOREBOARD OFFLINE':'SCOREBOARD NOT SET UP YET'));return}
    if(!list.length){box.appendChild(el('p','jsmall','NO SCORES YET. BE THE FIRST.'));return}
    var ol=el('ol','jboard');
    list.slice(0,n||10).forEach(function(r,i){var li=el('li',me&&String(r.name).toLowerCase()===me.toLowerCase()?'me':null);
      li.appendChild(el('b',null,(i+1)+'.'));li.appendChild(el('span',null,String(r.name)));
      li.appendChild(el('i',null,r.secs?Math.floor(r.secs/60)+':'+('0'+r.secs%60).slice(-2):''));li.appendChild(el('em',null,String(r.score)));ol.appendChild(li)});
    box.appendChild(ol);
  }
  function title(){
    state='title';
    var box=el('div','jbox jtitle');
    box.appendChild(el('p','jsmall','A PARODY · WEEK '+D.week+' POWER RANKINGS'));
    box.appendChild(el('h3','jlogo','SEMICONDUCTOR CEO SIMULATOR'));
    box.appendChild(el('p','jtxt','You run a totally normal chip company. Grab the GPUs and route them through '+N+' Singapore shell companies, one per team, worst to first. Do not get distracted by the beautiful women. Stomp the Commerce Department auditors. Stay out of the export controls.'));
    var c=el('p','jkeys');c.textContent='← → move · SPACE / ↑ jump · tap the buttons on a phone';box.appendChild(c);
    var row=el('div','jrow');row.appendChild(btn('PRESS START',start,'go'));
    var sk=el('a','jskip','Skip to the rankings');sk.href='#rankings';row.appendChild(sk);
    box.appendChild(row);
    if(SB){var tb=el('div','jtop');tb.appendChild(el('p','jsmall jg','TOP SCORES · WEEK '+D.week));var bl=el('div');bl.appendChild(el('p','jsmall','LOADING...'));tb.appendChild(bl);box.appendChild(tb);
      sbGet(function(l){boardInto(bl,l,myName(),5)})}
    if(best)box.appendChild(el('p','jsmall','YOUR BEST: '+best));
    show([box],start);
  }
  function start(){reset(true);hide();state='play';snd('coin');if(NARROW)try{cv.parentElement.parentElement.scrollIntoView({block:'start',behavior:'smooth'})}catch(_){}}
  function card(sh,got){
    state='card';var t=sh.team;
    var box=el('div','jbox jcard');
    box.appendChild(el('p','jsmall jg','SINGAPORE SHELL CO. '+(sh.idx+1)+' OF '+N+' · '+(got?got+' GPU'+(got===1?'':'S')+' RECEIVED':'0 GPUS (BOLD)')));
    var hd=el('div','jhd');
    if(t.logo){var im=el('img');im.src=t.logo;im.alt='';hd.appendChild(im)}
    var nm=el('div');nm.appendChild(el('p','jrank','#'+t.rank+(t.mv>0?'  ▲'+t.mv:t.mv<0?'  ▼'+(-t.mv):'')));
    nm.appendChild(el('h3','jname',t.shell||(t.name+' Pte. Ltd.')));
    nm.appendChild(el('p','jmeta',t.owner+' · '+t.rec+' · '+t.pts+' pts'));
    hd.appendChild(nm);box.appendChild(hd);
    if(t.line)box.appendChild(el('p','jtxt',t.line));
    var row=el('div','jrow');var go=sh.last?finish:resume;
    row.appendChild(btn(sh.last?'FINAL STANDINGS ▶':'CONTINUE ▶',go,'go'));
    if(t.anchor){var a=el('a','jskip','Full write-up');a.href='#'+t.anchor;row.appendChild(a)}
    box.appendChild(row);
    show([box],go);
  }
  function resume(){hide();state='play';P.jHeld=true;K.j=0}
  function over(){
    state='over';
    var box=el('div','jbox');
    box.appendChild(el('h3','jlogo red','GPUs SEIZED'));
    box.appendChild(el('p','jtxt','Out of leather jackets. '+shipped+' GPUs made it out before the feds did.'));
    var row=el('div','jrow');
    row.appendChild(btn('CONTINUE ▶',function(){lives=3;carry=0;reset(false);hide();state='play'},'go'));
    row.appendChild(btn('RESTART',start));
    box.appendChild(row);
    show([box],null);
    primary=function(){lives=3;carry=0;reset(false);hide();state='play'};
  }
  function myName(){try{return localStorage.getItem('jg-name')||''}catch(_){return ''}}
  function finish(){
    state='done';
    var secs=Math.floor(ticks/60), tb=Math.max(0,150-secs)*20, lb=lives*500;
    score+=tb+lb;
    var nb=score>best;if(nb){best=score;try{localStorage.setItem('jg-best-'+D.week,String(best))}catch(_){}}
    var box=el('div','jbox jwin');
    box.appendChild(el('p','jsmall jg','ALL '+N+' SHELL COMPANIES FUNDED'));
    box.appendChild(el('h3','jlogo','THE MORE YOU SHIP'));
    var st=el('dl','jstats');
    [['GPUs diverted',shipped+' / '+total],['Auditors stomped',String(stomps)],['Time',clock()],['Speed bonus','+'+tb],['Jackets left','+'+lb],[nb?'Score · new best':'Score',String(score)]].forEach(function(r,i){
      var d=el('div',i===5?'tot':null);d.appendChild(el('dt',null,r[0]));d.appendChild(el('dd',null,r[1]));st.appendChild(d)});
    box.appendChild(st);
    var bl=el('div','jtop');
    if(SB){
      var f=el('form','jform');
      var inp=el('input');inp.type='text';inp.maxLength=12;inp.placeholder='YOUR NAME';inp.value=myName();inp.autocomplete='nickname';inp.setAttribute('aria-label','Your name');
      var sub=el('button','jbtn go','SUBMIT');sub.type='submit';
      f.appendChild(inp);f.appendChild(sub);
      f.addEventListener('submit',function(ev){ev.preventDefault();
        var nm=inp.value.replace(/[^\w .'-]/g,'').trim().slice(0,12);if(!nm){inp.focus();return}
        try{localStorage.setItem('jg-name',nm)}catch(_){}
        sub.disabled=true;inp.disabled=true;sub.textContent='SENDING...';
        sbPost({week:D.week,name:nm,score:score,shipped:shipped,secs:secs},function(l){
          if(l===null){sub.disabled=false;inp.disabled=false;sub.textContent='RETRY';return}
          f.replaceWith(el('p','jsmall jg','SCORE POSTED'));boardInto(lb2,l,nm,10)})});
      box.appendChild(f);
    }
    bl.appendChild(el('p','jsmall jg','TOP 10 · WEEK '+D.week));
    var lb2=el('div');lb2.appendChild(el('p','jsmall',SB?'LOADING...':'SCOREBOARD NOT SET UP YET'));bl.appendChild(lb2);box.appendChild(bl);
    if(SB)sbGet(function(l){boardInto(lb2,l,myName(),10)});
    var row=el('div','jrow');row.appendChild(btn('PLAY AGAIN',start));
    var a=el('a','jskip','Read the rankings');a.href='#rankings';row.appendChild(a);
    box.appendChild(row);
    show([box],null);
    var fi=box.querySelector('input');if(fi&&inView&&!NARROW)try{fi.focus({preventScroll:true})}catch(_){}
    snd('ship');
  }

  // ---------- input ----------
  var KEYS={ArrowLeft:'l',KeyA:'l',ArrowRight:'r',KeyD:'r',ArrowUp:'j',KeyW:'j',Space:'j',KeyZ:'j',KeyK:'j'};
  document.addEventListener('keydown',function(e){
    if(!inView)return;
    var tag=(e.target&&e.target.tagName)||'';
    if(state!=='play'){
      if((e.code==='Enter'||e.code==='Space')&&primary&&tag!=='A'&&tag!=='BUTTON'&&tag!=='INPUT'){e.preventDefault();primary()}
      return;
    }
    var k=KEYS[e.code];if(k){K[k]=1;e.preventDefault()}
  });
  document.addEventListener('keyup',function(e){var k=KEYS[e.code];if(k)K[k]=0});
  window.addEventListener('blur',function(){K.l=K.r=K.j=0});
  document.querySelectorAll('[data-jk]').forEach(function(b){
    var k=b.getAttribute('data-jk');
    function dn(e){e.preventDefault();if(k==='j'&&state!=='play'&&primary){primary();return}K[k]=1;b.classList.add('on')}
    function up(e){K[k]=0;b.classList.remove('on')}
    b.addEventListener('pointerdown',dn);b.addEventListener('pointerup',up);b.addEventListener('pointercancel',up);b.addEventListener('pointerleave',up);
    b.addEventListener('contextmenu',function(e){e.preventDefault()});
  });
  var mb=document.getElementById('jgmute');
  function mlabel(){if(mb)mb.textContent=muted?'SOUND OFF':'SOUND ON'}
  if(mb){mlabel();mb.addEventListener('click',function(){muted=!muted;try{localStorage.setItem('jg-muted',muted?'1':'0')}catch(_){}mlabel()})}
  if('IntersectionObserver' in window){
    new IntersectionObserver(function(es){inView=es[0].isIntersecting;if(!inView){K.l=K.r=K.j=0}},{threshold:.35}).observe(cv);
  }

  // ---------- loop ----------
  var acc=0,lastT=0;
  function loop(ts){
    var dt=Math.min(100,ts-(lastT||ts));lastT=ts;
    if(state==='play'&&inView&&!document.hidden){acc+=dt;while(acc>=16.67){step();acc-=16.67;if(state!=='play'){acc=0;break}}}
    else{acc=0;if(state==='title'){frame++;cam=(cam+.4)%(LEVEL-W)}}
    draw();
    requestAnimationFrame(loop);
  }
  function boot(){title();requestAnimationFrame(loop)}
  if(document.fonts&&document.fonts.load){
    Promise.all([document.fonts.load('24px "Press Start 2P"'),document.fonts.load('15px Silkscreen')]).then(boot,boot);
  } else boot();
  window.__jg={get state(){return state},K:K,get P(){return P},get L(){return L},start:start,get next(){return next},get shipped(){return shipped},get score(){return score},get ticks(){return ticks}};
})();
