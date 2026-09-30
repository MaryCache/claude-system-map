"""Claude System Map の文字ロゴ（案4「l が線になる」）を、Inter の実際の字形から組んで SVG に書き出す。

形: 「Claude System Map」を Inter SemiBold で組み、Claude の l だけを差し色の線に置き換える。
線は l の縦画としてそのまま降り、ディセンダーの下で直角に右へ折れて、単語全体の下を p の右端まで抜ける。
シンボル（層を貫いた線が最後に右へ折れて出ていく）と同じ筋書きを文字の中に入れた。角を丸めないのもシンボルに合わせた。
方向は GPT Image のラフ（assets/logo/raw/wordmark-roughs-01.png の 4・git 管理外）から選び、字形は本物のフォントから取る
（design-library/knowledge/logo/wordmark.md 芯1「LLM に曲線を描かせない」）。

動かす前提で部品を分けて書き出す（knowledge/logo/checks.md「真実源は部品に分けたベクター」）:
  #wm-claude / #wm-system / #wm-map … 単語ごとの <g>、中の各字は .wm-ch
  #wm-spine（l の縦画から降りる線）/ #wm-elbow（右へ折れて抜ける線）… 支点はそれぞれ上端・左端

使い方: ~/.venvs/tools/bin/python build/wordmark.py
字形の取り出しは design-library の logo-lab/type/glyphs.py（uharfbuzz）に任せる。
フォント: Inter（SIL OFL 1.1）。ロゴへの加工は OFL 上で可（wordmark.md のライセンス表）。
"""

import os
import sys

sys.path.insert(0, os.path.expanduser('~/design-library/tools/logo-lab/type'))
from glyphs import shape  # noqa: E402

FONT = '/mnt/d/MaryCache/創作/font-library/archives/google-fonts-core-2026-07-16/Inter.ttf'
# 表示サイズ用の opsz 32 を使う（本文用の 14 は縦画が太く、ロゴの大きさでは重く見える）
AXES = {'wght': 600, 'opsz': 32}
INK = '#4B413A'
TERRA = '#C25A3F'
TEXT = 'Claude System Map'
# 字間。表示サイズの Inter は元から詰め気味なので、わずかに詰めるだけにする（em 比）
TRACKING = -0.012
# 語間を既定の空白の何倍にするか。ロゴでは語が離れすぎると3つの札に見えるため少し詰める
SPACE_SCALE = 0.86
# ディセンダー（y・p の下端）と、右へ折れた線とのすき間（em 比）。線が字に触れて見えない最小に近い値
ELBOW_GAP = 0.075
# 横に折れた線を縦画より細くする倍率。同じ太さの水平線は太って見える（wordmark.md「縦横の太さ」・Briem）
ELBOW_THIN = 0.88
# ペアごとの字間の手直し（em 比）。C は右が開いていて白が多く、C と線の間が線と a の間より広く見えたため詰める。
# 値は 2026-09-30 に 900px 幅で目視して決めた
PAIR_ADJUST = {'Cl': -0.02}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    run = shape(FONT, TEXT, AXES, tracking=TRACKING, pair_adjust=PAIR_ADJUST, space_scale=SPACE_SCALE)
    upm = run.upm
    l = next(g for g in run.glyphs if g.char == 'l')
    stem_l, stem_r = l.x + l.bounds[0], l.x + l.bounds[2]
    stem_w = stem_r - stem_l
    cap_top = l.bounds[1]  # y 下向きなので負

    inked = [g for g in run.glyphs if g.bounds]
    desc = max(g.bounds[3] for g in inked)  # ディセンダーの最下端（y 下向きで最大）
    right = max(g.x + g.bounds[2] for g in inked)
    elbow_top = desc + ELBOW_GAP * upm
    elbow_bottom = elbow_top + stem_w * ELBOW_THIN

    pad = round(stem_w / 2)
    min_x = min(0, stem_l) - pad
    top = cap_top - pad
    w = round(right - min_x + pad, 1)
    h = round(elbow_bottom + pad - top, 1)

    words = {'claude': [], 'system': [], 'map': []}
    keys = list(words)
    wi = 0
    for g in run.glyphs:
        if g.char == ' ':
            wi += 1
            continue
        if g.char == 'l':
            continue
        tx, ty = round(g.x - min_x, 1), round(-top, 1)
        # 位置は外側の <g> に持たせる。CSS の入場アニメーションは .wm-ch の transform を動かすので、
        # path 自身に transform 属性を付けると上書きされて字が原点へ集まる
        words[keys[wi]].append(f'<g transform="translate({tx} {ty})"><path class="wm-ch" d="{g.d}"/></g>')

    def rect(x1, y1, x2, y2):
        fx = lambda v: round(v - min_x, 1)
        fy = lambda v: round(v - top, 1)
        return f'M{fx(x1)} {fy(y1)}H{fx(x2)}V{fy(y2)}H{fx(x1)}Z'

    spine = rect(stem_l, cap_top, stem_r, elbow_top)
    # 折れは縦線の左端から始めて角を四角く閉じる（縦線と重ねて継ぎ目を出さない）
    elbow = rect(stem_l, elbow_top, right, elbow_bottom)
    src = run.font
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Claude System Map">\n'
        f'<!-- 字形: {src["family"]} {src["version"]} wght {AXES["wght"]} opsz {AXES["opsz"]} / {src["license"][:60]} -->\n'
        f'<g class="wm-letters" fill="{INK}">\n'
        + ''.join(f'<g id="wm-{k}">{"".join(v)}</g>\n' for k, v in words.items())
        + '</g>\n'
        f'<path id="wm-spine" class="wm-spine" fill="{TERRA}" d="{spine}"/>\n'
        f'<path id="wm-elbow" class="wm-elbow" fill="{TERRA}" d="{elbow}"/>\n'
        '</svg>\n'
    )
    out = os.path.join(ROOT, 'assets', 'logo', 'system-map-wordmark.svg')
    open(out, 'w', encoding='utf-8').write(svg)
    print('wrote', out, f'{w}x{h}', 'stem', round(stem_w, 1))


if __name__ == '__main__':
    main()
