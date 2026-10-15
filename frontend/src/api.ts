export type HeatwaveAnalysis = {
  location: { latitude: number; longitude: number; label: string | null };
  period: { start_year: number; end_year: number };
  data_source: { name: string; model: string; variable: string; unit: string };
  baseline: {
    start_year: number;
    end_year: number;
    percentile: number;
    method: string;
    valid_days: number;
    expected_days: number;
    coverage_percent: number;
  };
  threshold_celsius: number;
  data_quality: {
    expected_days: number;
    observed_days: number;
    missing_days: number;
    excluded_invalid_observations: number;
  };
  total_events: number;
  summary: {
    mean_event_duration_days: number | null;
    mean_event_intensity_celsius: number | null;
  };
  annual_metrics: Array<{
    year: number;
    event_count: number;
    mean_duration_days: number | null;
    max_duration_days: number | null;
    mean_intensity_celsius: number | null;
    data_available: boolean;
  }>;
  insight: {
    text: string;
    trend_direction: "increasing" | "decreasing" | "stable" | "unavailable";
    trend_slope_events_per_year: number | null;
  };
  caveats: string[];
  cache: { hit: boolean; generated_at: string | null };
};

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

export async function fetchHeatwaveAnalysis(
  input: {
    latitude: number;
    longitude: number;
    startYear: number;
    endYear: number;
    locationLabel: string;
  },
  signal?: AbortSignal,
): Promise<HeatwaveAnalysis> {
  const params = new URLSearchParams({
    latitude: String(input.latitude),
    longitude: String(input.longitude),
    start_year: String(input.startYear),
    end_year: String(input.endYear),
    location_label: input.locationLabel,
  });
  const response = await fetch(`${apiBase}/analysis/heatwaves?${params}`, { signal });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = body?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((item) => {
                if (typeof item === "object" && item !== null && "msg" in item) {
                  return String(item.msg);
                }
                return String(item);
              })
              .join(" ")
          : `Analysis request failed (${response.status})`;
    throw new Error(message);
  }
  return response.json() as Promise<HeatwaveAnalysis>;
}
