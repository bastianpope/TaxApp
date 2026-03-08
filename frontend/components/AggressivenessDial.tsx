"use client";

import type { AggressivenessLevel } from "@/lib/types";

const CONFIG: Record<AggressivenessLevel, { emoji: string; label: string; color: string; angle: number }> = {
  LOW: { emoji: "🛡️", label: "Conservative", color: "#10b981", angle: 220 },
  MEDIUM: { emoji: "⚖️", label: "Moderate", color: "#f59e0b", angle: 270 },
  HIGH: { emoji: "🚀", label: "Aggressive", color: "#ef4444", angle: 320 },
};

function svgPt(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180;
  return {
    x: Number((cx + r * Math.cos(rad)).toFixed(4)),
    y: Number((cy + r * Math.sin(rad)).toFixed(4)),
  };
}

export default function AggressivenessDial({ level }: { level: AggressivenessLevel }) {
  const { emoji, label, color, angle } = CONFIG[level];
  const r = 44;
  const cx = 70;
  const cy = 70;

  const tip = svgPt(cx, cy, r, angle);
  const perpRad = (angle * Math.PI) / 180 + Math.PI / 2;
  const base1 = {
    x: Number((cx + 4 * Math.cos(perpRad)).toFixed(4)),
    y: Number((cy + 4 * Math.sin(perpRad)).toFixed(4)),
  };
  const base2 = {
    x: Number((cx - 4 * Math.cos(perpRad)).toFixed(4)),
    y: Number((cy - 4 * Math.sin(perpRad)).toFixed(4)),
  };

  return (
    <div className="flex flex-col items-center gap-3">
      {/* suppressHydrationWarning is a safety-net; toFixed(4) should eliminate mismatches */}
      <svg
        suppressHydrationWarning
        viewBox="0 0 140 100"
        className="w-36 h-24"
        aria-label={`Aggressiveness: ${label}`}
      >
        {/* Background arc segments */}
        {(["#10b981", "#f59e0b", "#ef4444"] as const).map((c, i) => {
          const startA = 200 + i * 40;
          const endA = startA + 40;
          const s = svgPt(cx, cy, r, startA);
          const e = svgPt(cx, cy, r, endA);
          return (
            <path
              key={c}
              d={`M ${s.x} ${s.y} A ${r} ${r} 0 0 1 ${e.x} ${e.y}`}
              fill="none"
              stroke={c}
              strokeWidth="6"
              strokeLinecap="round"
              opacity={c === color ? 1 : 0.25}
            />
          );
        })}
        {/* Needle */}
        <polygon
          suppressHydrationWarning
          points={`${tip.x},${tip.y} ${base1.x},${base1.y} ${base2.x},${base2.y}`}
          fill={color}
        />
        {/* Center hub */}
        <circle cx={cx} cy={cy} r={4} fill="var(--bg-card)" stroke={color} strokeWidth="2" />
        {/* Label */}
        <text x={cx} y={cy + 20} textAnchor="middle" fill={color} fontSize="9" fontWeight="700">
          {label}
        </text>
      </svg>
      <span className="text-2xl">{emoji}</span>
    </div>
  );
}
