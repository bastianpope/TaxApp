"use client";

const THRESHOLDS = [
  { max: 30, label: "Low", color: "#10b981" },
  { max: 60, label: "Medium", color: "#f59e0b" },
  { max: 100, label: "High", color: "#ef4444" },
];

function getColor(score: number) {
  for (const t of THRESHOLDS) {
    if (score <= t.max) return { color: t.color, label: t.label };
  }
  return { color: "#ef4444", label: "High" };
}

export default function RiskGauge({ score }: { score: number }) {
  const { color, label } = getColor(score);
  const pct = Math.min(100, Math.max(0, score));
  const r = 52;
  const cx = 80;
  const cy = 76;
  const startAngle = 200;
  const range = 140;

  function arcPoint(angle: number, radius: number) {
    return {
      x: cx + radius * Math.cos((angle * Math.PI) / 180),
      y: cy + radius * Math.sin((angle * Math.PI) / 180),
    };
  }

  function describeArc(start: number, span: number, radius: number) {
    const s = arcPoint(start, radius);
    const e = arcPoint(start + span, radius);
    const large = span > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${radius} ${radius} 0 ${large} 1 ${e.x} ${e.y}`;
  }

  const needleAngle = startAngle + pct / 100 * range;
  const needleRad = (needleAngle * Math.PI) / 180;
  const nx = cx + (r - 6) * Math.cos(needleRad);
  const ny = cy + (r - 6) * Math.sin(needleRad);

  return (
    <div className="flex flex-col items-center gap-2">
      <svg viewBox="0 0 160 100" className="w-44 h-28" aria-label={`Audit risk: ${score} out of 100`}>
        <path d={describeArc(startAngle, range, r)} fill="none" stroke="var(--border)" strokeWidth="8" strokeLinecap="round" />
        {pct > 0 && <path d={describeArc(startAngle, pct / 100 * range, r)} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" />}
        <circle cx={nx} cy={ny} r={6} fill={color} />
        <text x={cx} y={cy + 8} textAnchor="middle" fill="white" fontSize="20" fontWeight="700">{score}</text>
        <text x={cx} y={cy + 20} textAnchor="middle" fill={color} fontSize="8" fontWeight="600">{label} Risk</text>
        {[
          { angle: startAngle, text: "0" },
          { angle: startAngle + range / 2, text: "50" },
          { angle: startAngle + range, text: "100" },
        ].map(({ angle, text }) => {
          const p = arcPoint(angle, r + 10);
          return <text key={text} x={p.x} y={p.y} textAnchor="middle" fill="#64748b" fontSize="7">{text}</text>;
        })}
      </svg>
      <div className="flex gap-3">
        {THRESHOLDS.map((t) => (
          <div key={t.label} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: t.color }} />
            <span className="text-xs text-slate-400">{t.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
