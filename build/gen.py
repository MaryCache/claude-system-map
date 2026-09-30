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

logo=open(f'{ROOT}/assets/logo/system-map-symbol.svg',encoding='utf-8').read().strip()
s=s.replace('{{LOGO_SVG}}',logo.replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">','<svg viewBox="0 0 100 100" aria-hidden="true">'))

# 小さなモネ：ドット絵（assets/monet/pixel/）を優先。見出しごとに別の表情・仕草にする（かしぇ 2026-09-30）。場面に合う名前のものが無ければ monet-idle、
# それも無ければシートの切り抜き（円の窓）に倒す。raw/ は使わない。
pixels=sorted(p for p in glob.glob(f'{ROOT}/assets/monet/pixel/*.png'))
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
