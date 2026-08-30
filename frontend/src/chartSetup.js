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
