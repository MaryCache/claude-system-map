"""index.src.html から index.html を作る。
assets/illust/ と assets/monet/pixel/ に実在する素材だけを参照し、無いものは出さない（別の切り抜きに倒す）。
素材が増えたらこのスクリプトを再実行する（~/.venvs/tools/bin/python build/gen.py）。
ページの本体を直すときは index.html ではなく build/index.src.html を直す（index.html は毎回上書きされる）。"""
import os, re, glob
from PIL import Image
# リポジトリの根（このスクリプトは build/ にある）
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(os.path.dirname(os.path.abspath(__file__)),'index.src.html')
s=open(SRC,encoding='utf-8').read()

ICONS={1:'file-text',2:'database',3:'zap',4:'cog',5:'git-fork',6:'clipboard-check',7:'scale'}
NAMES={1:'静的設定',2:'記憶',3:'自動で動くしくみ',4:'実行',5:'外部モデルワーカー',6:'運用・自己点検',7:'判断のルール'}
found=[]
for n in range(1,8):
    f=next((f'assets/illust/layer-{n}.{e}' for e in ('webp','png') if os.path.exists(f'{ROOT}/assets/illust/layer-{n}.{e}')),None)
    if f:
        found.append(f)
        node=f'<img class="thumb" src="{f}" alt="" width="40" height="40" loading="lazy">'
        det=f'<img class="ld-illust" src="{f}" alt="層「{NAMES[n]}」の挿絵" width="96" height="96" loading="lazy">'
    else:
        node=''
        det=f'<span class="ld-icon"><svg class="icon" aria-hidden="true"><use href="#i-{ICONS[n]}"/></svg></span>'
    s=s.replace('{{ILLUST_NODE_%d}}'%n,node).replace('{{ILLUST_DETAIL_%d}}'%n,det)

tile='assets/illust/paper-tile.webp' if os.path.exists(f'{ROOT}/assets/illust/paper-tile.webp') else None
s=s.replace('  /* PAPER_TILE */\n', f'  background-image:url("{tile}");background-size:600px 600px;\n' if tile else '')

# ヘッダーはシンボル＋文字ロゴ（一度は文字ロゴだけにしたが、かしぇ「左にもともとのロゴもほしい」2026-09-30）。
# シンボルは動かすために部品へ分ける：横棒（本文色）／縦の線／右へ折れる線。logo-lab の書き出しは差し色を1本のパス
# （縦線と折れの2つの部分パス）で出すので、Z の直後の M で割る。割れない形なら差し色は1本のまま使う
sym=open(f'{ROOT}/assets/logo/system-map-symbol.svg',encoding='utf-8').read().strip()
sym=sym.replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">','<svg class="brand-symbol" viewBox="0 0 100 100" aria-hidden="true" focusable="false">')
m=re.search(r'<path fill="(#[0-9A-Fa-f]{6})" d="([^"]+)"/><path fill="(#[0-9A-Fa-f]{6})" d="([^"]+)"/>',sym)
if m:
    parts=[p.strip() for p in re.split(r'Z\s*(?=M)',m[4]) if p.strip()]
    parts=[p if p.endswith('Z') else p+' Z' for p in parts]
    acc=(f'<path class="sy-spine" fill="{m[3]}" d="{parts[0]}"/><path class="sy-elbow" fill="{m[3]}" d="{parts[1]}"/>'
         if len(parts)==2 else f'<path class="sy-spine" fill="{m[3]}" d="{m[4]}"/>')
    sym=sym.replace(m[0],f'<path class="sy-bars" fill="{m[1]}" d="{m[2]}"/>'+acc)
    # ホバーで光を走らせる道筋（縦線の中心を降り、折れの中心で右へ）。部分パスの頂点から寸法を取る
    if len(parts)==2:
        num=lambda p:[float(v) for v in re.findall(r'-?[\d.]+',p)]
        sx,sy=num(parts[0])[0::2],num(parts[0])[1::2]
        ex,ey=num(parts[1])[0::2],num(parts[1])[1::2]
        cx=(min(sx)+max(sx))/2; cy=(min(ey)+max(ey))/2
        w=min(max(sx)-min(sx),max(ey)-min(ey))
        sym=sym.replace('</svg>',f'<path class="flow sy-flow" fill="none" stroke-width="{w:.2f}" pathLength="100" d="M{cx:.2f} {min(sy):.2f}V{cy:.2f}H{max(ex):.2f}"/></svg>')
s=s.replace('{{SYMBOL_SVG}}',sym)
# リンク側に aria-label があるので、埋め込む SVG は読み上げから外す。部品の id（wm-*）はページ内で一意なのでそのまま残し、動きの CSS から指す
wm=open(f'{ROOT}/assets/logo/system-map-wordmark.svg',encoding='utf-8').read().strip()
wm=wm.replace('xmlns="http://www.w3.org/2000/svg" ','').replace(' role="img" aria-label="Claude System Map"',' aria-hidden="true" focusable="false"')
s=s.replace('{{WORDMARK_SVG}}',wm)

# 小さなモネ：ドット絵（assets/monet/pixel/）を優先。見出しごとに別の表情・仕草にする（かしぇ 2026-09-30）。場面に合う名前のものが無ければ monet-idle、
# それも無ければシートの切り抜き（円の窓）に倒す。raw/ は使わない。
# ちびモネ（monet-chibi-*）は monet mod のパネル用。名前順で先に来て見出しの立ち絵に化けるので外す
pixels=sorted(p for p in glob.glob(f'{ROOT}/assets/monet/pixel/*.png') if 'chibi' not in os.path.basename(p))
def pick_pixel(keys):
    for k in keys:
        for p in pixels:
            if k in os.path.basename(p): return p
    return None
SLOTS={
 'fig-b':(['smile'],'face-smile','微笑むモネ'),
 'fig-c':(['think'],'face-think','考え中のモネ'),
 'fig-d':(['point','explain'],'face-explain','指さしで説明するモネ'),
 'fig-e':(['book'],'face-neutral','本を開いて見ているモネ'),
 'lists':(['present'],'face-neutral','こちらですと手で示すモネ'),
 'foot':(['wave'],'icon-face','手を振るモネ'),
 'empty':(['worry'],'face-worry',''),
}
used={}
for slot,(keys,cut,alt) in SLOTS.items():
    p=pick_pixel(keys) or (pick_pixel(['idle']) if slot not in ('empty',) else None)
    if p:
        im=Image.open(p); w,h=im.size
        a=im.getchannel('A') if im.mode in ('RGBA','LA') else im.convert('RGBA').getchannel('A')
        bb=a.getbbox() or (0,0,w,h)
        rows=round(h*0.42)
        # SP 用の顔の窓：上から 34% の行、幅は不透明部分の中央 60%
        # SP 用の顔の窓：上から 34% の行。幅は、その行の範囲に実際に描かれている部分（髪・リボンの房まで）に合わせる。
        # 全身の幅の中央 62% で切ると、リボンの房と髪の端が見切れた（2026-09-30 スマホで確認）
        hrows=round(h*0.42)  # 胸の前の仕草（本・合わせた手）まで入れる。0.34 だと顔だけになり表情違いが分かりにくかった
        hb=a.crop((0,0,w,hrows)).getbbox() or bb
        hdx=hb[0]; hw=max(24,hb[2]-hb[0])
        rel='assets/monet/pixel/'+os.path.basename(p)
        alt_txt = alt or 'モネ'
        html=(f'<div class="sprite" style="--w:{w};--h:{h};--rows:{rows};--hw:{hw};--hdx:{hdx};--hrows:{hrows}">'
              f'<img src="{rel}" width="{w}" height="{h}" alt="{alt_txt}（ドット絵）" loading="lazy"></div>')
        if slot=='empty': html=f'<div class="sprite" style="--w:{w};--h:{h};--rows:{round(h*0.3)};--s:2;border:0"><img src="{rel}" width="{w}" height="{h}" alt=""></div>'
        used[slot]=rel
    else:
        if slot=='empty':
            html=f'<img src="assets/monet/cut/{cut}.webp" alt="" width="64" height="64">'
        else:
            html=f'<div class="avatar"><img src="assets/monet/cut/{cut}.webp" alt="{alt}" loading="lazy"></div>'
        used[slot]=cut
    s=s.replace('{{MONET %s}}'%slot, html if slot in ('empty','foot') else '      '+html)

left=re.findall(r'\{\{[A-Z][^}]*\}\}',s)
assert not left, left
open(f'{ROOT}/index.html','w',encoding='utf-8').write(s)
print('illust:',found,'| tile:',tile,'| monet:',used)
