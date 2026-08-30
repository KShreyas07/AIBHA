const LABEL_COLORS = {
  Excellent: "#22c55e",
  Good: "#84cc16",
  Average: "#f59e0b",
  Poor: "#f97316",
  Critical: "#ef4444",
};

export default function HealthGauge({ score = 0, label = "N/A" }) {
  const clamped = Math.max(0, Math.min(100, score));
  const angle = (clamped / 100) * 180;
  const radius = 80;
  const cx = 100;
  const cy = 100;
  const toRad = (deg) => ((180 - deg) * Math.PI) / 180;
  const x = cx + radius * Math.cos(toRad(angle));
  const y = cy - radius * Math.sin(toRad(angle));
  const largeArc = angle > 180 ? 1 : 0;
  const color = LABEL_COLORS[label] || "#6366f1";

  return (
    <div className="flex flex-col items-center">
      <svg width="200" height="120" viewBox="0 0 200 120">
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#EEE7D7" strokeWidth="16" strokeLinecap="round" />
        <path
          d={`M 20 100 A 80 80 0 ${largeArc} 1 ${x} ${y}`}
          fill="none"
          stroke={color}
          strokeWidth="16"
          strokeLinecap="round"
        />
      </svg>
      <p className="-mt-6 font-display text-3xl font-bold text-ink-900">{Math.round(clamped)}</p>
      <p className="text-sm font-medium" style={{ color }}>{label}</p>
    </div>
  );
}
