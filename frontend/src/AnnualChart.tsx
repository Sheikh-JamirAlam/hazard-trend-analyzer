import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { HeatwaveAnalysis } from "./api";

export function AnnualChart({ data }: { data: HeatwaveAnalysis["annual_metrics"] }) {
  const available = data.filter((item) => item.data_available);
  if (!available.length) {
    return (
      <div className="grid h-full place-items-center border border-dashed border-[#77776e] p-6 text-center font-mono text-xs uppercase tracking-wide text-[#62625b]">
        No annual observations are available for this period.
      </div>
    );
  }
  const chartData = data.map((item) => ({
    ...item,
    event_count: item.data_available ? item.event_count : null,
  }));

  return (
    <div className="h-full w-full" role="img" aria-label="Line chart showing annual heatwave event counts">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 16, right: 12, left: -20, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="#c9c7bf" strokeDasharray="3 5" />
          <XAxis dataKey="year" tickLine={false} axisLine={{ stroke: "#171714" }} tick={{ fill: "#62625b", fontSize: 10, fontFamily: "monospace" }} minTickGap={30} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: "#62625b", fontSize: 10, fontFamily: "monospace" }} width={40} />
          <Tooltip
            cursor={{ stroke: "#171714", strokeDasharray: "4 5" }}
            contentStyle={{ borderRadius: 0, border: "2px solid #171714", background: "#f4f4f0", fontFamily: "monospace", fontSize: 11 }}
            formatter={(value) => [`${String(value ?? "—")} events`, "Heatwaves"]}
            labelFormatter={(label) => `Year ${String(label)}`}
          />
          <Line
            type="monotone"
            dataKey="event_count"
            name="Heatwave events"
            stroke="#e61919"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "#e61919", strokeWidth: 0 }}
            activeDot={{ r: 5, stroke: "#f4f4f0", strokeWidth: 2 }}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
