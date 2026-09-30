// Claude System Map のシンボル（積み重なった層を、1本の線が貫いていく形）の作図ファイル。
// logo-lab（~/design-library/tools/logo-lab/）で開き、つまみで詰める。詰めた値は書き出した
// system-map.params.json を取り込んで下の value（初期値）へ反映する。
// ファイルの書式は ~/design-library/tools/logo-lab/README.md の「作図ファイルの書式」。
//
// 形容詞（DESIGN.md の意図から）: 精密・透けて見える・構造的・静か。
// 横棒＝設定・記憶・実行…と積み重なった層、縦の線＝依頼が層を通って委任先へ届く道筋、
// 線が最後に右へ折れて出ていく＝委任先へ振られる。意味は説明として添えるもので、形の必須条件にはしない
// （knowledge/logo/index.md「モネ既定」2）。地球・脳・回路基板・光る球体の定番は避けた。

const systemMap = {
	name: 'system-map',
	title: 'Claude System Map シンボル（層を貫く線）',

	params: {
		// ── 層（横棒）
		// 実際の層は7つだが、16px で横棒とすき間が 1px を下回らない本数を既定にした（下の checks で確かめる）
		count: { label: '層の数', group: '層', min: 3, max: 7, step: 1, value: 3 },
		height: { label: '全高', group: '層', min: 50, max: 90, step: 0.5, value: 80 },
		width: { label: '横幅', group: '層', min: 50, max: 90, step: 0.5, value: 74 },
		// 層の太さに対するすき間の比。小さいほど塊に、大きいほど縞に見える
		gapRatio: { label: 'すき間（層の太さ比）', group: '層', min: 0.3, max: 1.2, step: 0.05, value: 0.8 },
		// 右端を下の層ほど短くずらす量。0 で揃った四角、上げるほど階段になり「一覧」から「図」に寄る
		stagger: { label: '右端の段差', group: '層', min: 0, max: 15, step: 0.25, value: 8 },

		// ── 貫く線（アクセント）
		traceX: { label: '線の横位置（%）', group: '線', min: 20, max: 80, step: 0.5, value: 34 },
		traceWeight: { label: '線の太さ', group: '線', min: 3, max: 14, step: 0.25, value: 7 },
		// 線の両脇で層を切るすき間。色がなくても「線が通っている」と読める幅にする
		traceGap: { label: '線の両脇のすき間', group: '線', min: 0, max: 8, step: 0.25, value: 6.5 },
		// 最下段を抜けたあと、線が右へ折れて出ていく長さ（横幅比 %）。
		// 折れがないと温度計や一覧アイコンに寄る（2026-09-30 の初版で確認）
		elbow: { label: '折れて出る長さ（%）', group: '線', min: 0, max: 60, step: 0.5, value: 40 },

		// ── 視覚補正（knowledge/logo/geometry.md 2章）
		// 同じ太さでは水平線が太く見えるため、横棒だけ細らせる倍率
		barCorrection: { label: '横棒の細め（倍）', group: '視覚補正', min: 0.85, max: 1, step: 0.005, value: 0.95 },
		// 幾何の中心は沈んで見えるため、全体を少し上へ上げる（高さ比 %）
		opticalLift: { label: '光学的中心（%）', group: '視覚補正', min: 0, max: 5, step: 0.1, value: 1.5 },

		// ── ロックアップ
		lockupSize: { label: 'シンボルの大きさ（px）', group: 'ロックアップ', min: 20, max: 48, step: 1, value: 30 },
		lockupGap: { label: '文字との間（px）', group: 'ロックアップ', min: 0, max: 20, step: 1, value: 10 },
	},

	// 配色はモネのカラー設定（assets/monet/README.md）＝ページと同じ。ページの地はアイボリー（light が主）。
	// dark はダークブラウンの面に置くときの版で、main をアイボリーに反転する
	themes: {
		light: { bg: '#F8F6F1', main: '#4B413A', accent: '#C25A3F' },
		dark: { bg: '#4B413A', main: '#F8F6F1', accent: '#C25A3F' },
	},

	lockup: {
		panelBg: '#F8F6F1',
		width: 260,
		paddingLeft: 12,
		kick: 'CLAUDE CODE',
		font: "'Inter', 'Noto Sans JP', sans-serif",
		fontSize: 22,
		fontWeight: 700,
		skewDeg: 0,
		parts: [
			{ text: 'SYSTEM', style: 'fill' },
			{ text: 'MAP', style: 'outline', strokeColor: '#C25A3F', strokeWidth: 1 },
		],
	},

	/**
	 * 値 p からシンボルを作図する。座標は 0〜100 の正方形。
	 * 手順: 全高を「層 × count ＋ すき間 × count ＋ 折れの太さ」に割り付ける → 各層を長方形で置き、
	 * 右端を段差ぶん短くする → 線の帯（線＋両脇のすき間）で各層を左右に切る → 線と、右へ折れる先を置く
	 * → 全体を中央へ寄せて光学的中心へ上げる。ブーリアン演算を使わず、長方形の分割だけで描く。
	 */
	build(p, g) {
		const n = Math.round(p.count);
		const elbowH = p.traceWeight;
		// 全高 = 層 n 本 + すき間 n 個（層どうし n−1 ＋ 最下段と折れの間 1。リズムを揃える）+ 折れの太さ
		const unit = (p.height - elbowH) / (n * (1 + p.gapRatio));
		const bar = unit * p.barCorrection;
		const gap = unit * p.gapRatio;
		const left = 50 - p.width / 2;
		const tx = left + (p.width * p.traceX) / 100;
		const cutL = tx - p.traceWeight / 2 - p.traceGap;
		const cutR = tx + p.traceWeight / 2 + p.traceGap;

		const rect = (x0, y0, x1, y1) => [
			[x0, y0],
			[x1, y0],
			[x1, y1],
			[x0, y1],
		];

		const bars = [];
		let lastBottom = 0;
		for (let i = 0; i < n; i++) {
			// 細めた分は層の枠の中で上下均等に削る（層の間隔＝リズムは変えない）
			const y = i * (unit + gap) + (unit - bar) / 2;
			const right = left + p.width - p.stagger * i;
			// 線の帯より左の部分と右の部分に分ける。段差で右端が帯にかかったら右の部分は出さない
			if (cutL > left) bars.push(rect(left, y, Math.min(cutL, right), y + bar));
			if (right > cutR) bars.push(rect(cutR, y, right, y + bar));
			lastBottom = i * (unit + gap) + unit;
		}
		const elbowTop = lastBottom + gap;
		const trace = rect(tx - p.traceWeight / 2, -gap, tx + p.traceWeight / 2, elbowTop + elbowH);
		const elbowRect = rect(tx - p.traceWeight / 2, elbowTop, tx + p.traceWeight / 2 + (p.width * p.elbow) / 100, elbowTop + elbowH);

		// 縦方向の外接（線の上端は最上段の上へ gap ぶん抜けて「上から来た」と読ませる）を中央へ
		const all = [...bars.flat(), ...trace, ...elbowRect];
		const b = g.bbox(all);
		const dx = 50 - (b.minX + b.w / 2);
		const dy = 50 - (b.minY + b.h / 2) - (p.opticalLift / 100) * p.height;
		const move = (pts) => g.translate(pts, dx, dy);

		const barsPath = bars.map((r) => g.polyPath(move(r))).join(' ');
		const px16 = (v) => (v * 16) / 100;
		return {
			layers: [
				{ id: 'layers', role: 'main', d: barsPath },
				{ id: 'trace', role: 'accent', d: `${g.polyPath(move(trace))} ${g.polyPath(move(elbowRect))}` },
			],
			guides: [
				{ d: g.polyPath(move(rect(left, 0, left + p.width, lastBottom))), label: '層の外枠' },
				{ d: 'M50 0 V100 M0 50 H100', label: '中心' },
			],
			checks: [
				{ label: '層の太さ @16px', value: `${px16(bar).toFixed(2)}px`, ok: px16(bar) >= 1 },
				{ label: '層のすき間 @16px', value: `${px16(gap).toFixed(2)}px`, ok: px16(gap) >= 1 },
				{ label: '線の両脇のすき間 @16px', value: `${px16(p.traceGap).toFixed(2)}px`, ok: px16(p.traceGap) >= 1 },
				{ label: '線の太さ @16px', value: `${px16(p.traceWeight).toFixed(2)}px`, ok: px16(p.traceWeight) >= 1 },
			],
		};
	},
};

export default systemMap;
