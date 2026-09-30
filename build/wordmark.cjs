/**
 * Claude System Map の文字ロゴ（案4「l が線になる」）を、Inter の実際の字形から組んで SVG に書き出す。
 *
 * 形: 「Claude System Map」を Inter SemiBold で組み、Claude の l だけを差し色の線に置き換える。
 * 線は l の縦画としてそのまま降り、ディセンダーの下で直角に右へ折れて、単語全体の下を p の右端まで抜ける。
 * シンボル（層を貫いた線が最後に右へ折れて出ていく）と同じ筋書きを文字の中に入れた。角を丸めないのもシンボルに合わせた。
 * 方向は GPT Image のラフ（assets/logo/raw/wordmark-roughs-01.png の 4）から選び、字形は本物のフォントから取る
 * （design-library/knowledge/logo/wordmark.md 芯1「LLM に曲線を描かせない」）。
 *
 * 動かす前提で部品を分けて書き出す（knowledge/logo/checks.md「真実源は部品に分けたベクター」）:
 *   #wm-claude / #wm-system / #wm-map … 単語ごとの <g>、中の各字は .wm-ch
 *   #wm-spine（l の縦画から降りる線）/ #wm-elbow（右へ折れて抜ける線）… 支点はそれぞれ上端・左端
 *
 * 使い方（2段）:
 *   1. Inter の可変フォントを太さ 600・opsz 32 の静的フォントにする（fontTools の instancer）
 *   2. NODE_PATH=<opentype.js のある node_modules> node build/wordmark.cjs <静的フォント.ttf>
 * フォント: Inter（SIL OFL 1.1）。ロゴへの加工は OFL 上で可（wordmark.md のライセンス表）。
 */
const fs = require('fs');
const path = require('path');
const opentype = require('opentype.js');

const fontPath = process.argv[2];
if (!fontPath) throw new Error('静的化した Inter（wght 600）の .ttf を引数に渡す');
const font = opentype.loadSync(fontPath);

const INK = '#4B413A';
const TERRA = '#C25A3F';
/** 字間。表示サイズ（opsz 32）の Inter は元から詰め気味なので、わずかに詰めるだけにする（em 比） */
const TRACKING = -0.012;
/** 語間を既定の空白の何倍にするか。ロゴでは語が離れすぎると3つの札に見えるため少し詰める */
const SPACE_SCALE = 0.86;
/** ディセンダー（y・p の下端）と、右へ折れた線とのすき間（em 比）。線が字に触れて見えない最小に近い値 */
const ELBOW_GAP = 0.075;
/** 横に折れた線を縦画より細くする倍率。同じ太さの水平線は太って見える（wordmark.md「縦横の太さ」・Briem） */
const ELBOW_THIN = 0.88;
/**
 * ペアごとの字間の手直し（em 比）。C は右が開いていて白が多く、C と線の間が線と a の間より広く見えたため詰める。
 * 値は 2026-09-30 に 900px 幅で目視して決めた
 */
const PAIR_ADJUST = { Cl: -0.02 };

const upm = font.unitsPerEm;
const text = 'Claude System Map';
const glyphs = font.stringToGlyphs(text);

// 並べる：カーニング（GPOS/kern から opentype.js が取れる分）＋字間。l は線に置き換えるので位置だけ記録する
let x = 0;
const placed = [];
glyphs.forEach((g, i) => {
	const ch = text[i];
	if (i > 0) x += font.getKerningValue(glyphs[i - 1], g) + (PAIR_ADJUST[text[i - 1] + ch] || 0) * upm;
	placed.push({ ch, g, x });
	const adv = ch === ' ' ? g.advanceWidth * SPACE_SCALE : g.advanceWidth;
	x += adv + TRACKING * upm;
});

const l = placed.find((p) => p.ch === 'l');
const lBox = l.g.getBoundingBox();
const stemL = l.x + lBox.x1;
const stemR = l.x + lBox.x2;
const stemW = stemR - stemL;
const capTop = lBox.y2;

// ディセンダーの最下端を実測し、その下に線を通す
let descMin = 0;
let right = 0;
for (const p of placed) {
	if (p.ch === ' ') continue;
	const b = p.g.getBoundingBox();
	descMin = Math.min(descMin, b.y1);
	right = Math.max(right, p.x + b.x2);
}
const elbowTop = descMin - ELBOW_GAP * upm;
const elbowBottom = elbowTop - stemW * ELBOW_THIN;

// フォント座標（y 上向き）→ SVG 座標（y 下向き）。余白は線の太さの半分
const pad = Math.round(stemW / 2);
const minX = Math.min(0, stemL) - pad;
const top = capTop + pad;
const toY = (y) => +(top - y).toFixed(1);
const toX = (xx) => +(xx - minX).toFixed(1);
const W = +(right - minX + pad).toFixed(1);
const H = +(top - elbowBottom + pad).toFixed(1);

const words = { claude: [], system: [], map: [] };
let wi = 0;
const keys = Object.keys(words);
for (const p of placed) {
	if (p.ch === ' ') { wi++; continue; }
	if (p.ch === 'l') continue;
	const d = p.g.getPath(p.x - minX, top, upm).toPathData(1);
	words[keys[wi]].push(`<path class="wm-ch" d="${d}"/>`);
}

const rect = (x1, y1, x2, y2) => `M${toX(x1)} ${toY(y1)}H${toX(x2)}V${toY(y2)}H${toX(x1)}Z`;
const spine = rect(stemL, capTop, stemR, elbowTop);
// 折れは縦線の左端から始めて角を四角く閉じる（縦線と重ねて継ぎ目を出さない）
const elbow = rect(stemL, elbowTop, right, elbowBottom);

const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Claude System Map">
<g class="wm-letters" fill="${INK}">
<g id="wm-claude">${words.claude.join('')}</g>
<g id="wm-system">${words.system.join('')}</g>
<g id="wm-map">${words.map.join('')}</g>
</g>
<path id="wm-spine" class="wm-spine" fill="${TERRA}" d="${spine}"/>
<path id="wm-elbow" class="wm-elbow" fill="${TERRA}" d="${elbow}"/>
</svg>
`;
const out = path.join(__dirname, '..', 'assets', 'logo', 'system-map-wordmark.svg');
fs.writeFileSync(out, svg);
console.log('wrote', out, `${W}x${H}`, 'stem', stemW, 'desc', descMin);
