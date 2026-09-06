import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  RadialLinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadarController,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(
  CategoryScale, LinearScale, RadialLinearScale, PointElement, LineElement, BarElement,
  ArcElement, RadarController, Title, Tooltip, Legend, Filler
);

export const CHART_COLORS = {
  brand: "#C2410C",
  green: "#3F7D4C",
  amber: "#C2850F",
  red: "#B4432F",
  slate: "#948A78",
};

export const baseLineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: "#453D31" } },
  },
  scales: {
    x: { ticks: { color: "#726755" }, grid: { color: "#EEE7D7" } },
    y: { ticks: { color: "#726755" }, grid: { color: "#EEE7D7" } },
  },
};

export const basePieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: "bottom", labels: { color: "#453D31" } },
  },
};

// Mirrors the axis weights in backend/app/ml/health_score.py — each raw point
// value is normalized to a 0-100 share of its own max so all six axes are
// comparable on one radar, regardless of how many points that axis is worth.
export const DNA_AXES = [
  { key: "revenue_growth", label: "Revenue Growth", max: 20 },
  { key: "profit_margin", label: "Profitability", max: 20 },
  { key: "cash_flow", label: "Cash Flow", max: 20 },
  { key: "inventory", label: "Inventory", max: 15 },
  { key: "debt", label: "Debt Health", max: 15 },
  { key: "customer_growth", label: "Customer Growth", max: 10 },
];

export function dnaRadarDataset(breakdown) {
  return {
    labels: DNA_AXES.map((a) => a.label),
    datasets: [
      {
        label: "Health",
        data: DNA_AXES.map((a) => Math.round(((breakdown?.[a.key] || 0) / a.max) * 100)),
        borderColor: CHART_COLORS.brand,
        backgroundColor: `${CHART_COLORS.brand}33`,
        pointBackgroundColor: CHART_COLORS.brand,
        fill: true,
      },
    ],
  };
}

export const radarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: {
      min: 0,
      max: 100,
      ticks: { display: false, stepSize: 25 },
      grid: { color: "#EEE7D7" },
      angleLines: { color: "#EEE7D7" },
      pointLabels: { color: "#453D31", font: { size: 11 } },
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.raw}%` } },
  },
};

// Two-dataset variant for the Digital Twin: baseline (dashed, faint) overlaid with
// the simulated what-if shape (solid), so the shift is visible axis by axis.
export function dnaTwinRadarDataset(baselineBreakdown, simulatedBreakdown) {
  const toPct = (breakdown) => DNA_AXES.map((a) => Math.round(((breakdown?.[a.key] || 0) / a.max) * 100));
  return {
    labels: DNA_AXES.map((a) => a.label),
    datasets: [
      {
        label: "What-if",
        data: toPct(simulatedBreakdown),
        borderColor: CHART_COLORS.brand,
        backgroundColor: `${CHART_COLORS.brand}33`,
        pointBackgroundColor: CHART_COLORS.brand,
        fill: true,
        order: 1,
      },
      {
        label: "Current",
        data: toPct(baselineBreakdown),
        borderColor: CHART_COLORS.slate,
        backgroundColor: "transparent",
        borderDash: [4, 4],
        pointBackgroundColor: CHART_COLORS.slate,
        fill: false,
        order: 2,
      },
    ],
  };
}

export const twinRadarOptions = {
  ...radarOptions,
  plugins: {
    legend: { display: true, position: "bottom", labels: { color: "#453D31", boxWidth: 12, font: { size: 11 } } },
    tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label} — ${ctx.label}: ${ctx.raw}%` } },
  },
};
