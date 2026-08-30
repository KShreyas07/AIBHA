import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

export const CHART_COLORS = {
  brand: "#6366f1",
  green: "#22c55e",
  amber: "#f59e0b",
  red: "#ef4444",
  slate: "#94a3b8",
};

export const baseLineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: "#cbd5e1" } },
  },
  scales: {
    x: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
    y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
  },
};

export const basePieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: "bottom", labels: { color: "#cbd5e1" } },
  },
};
