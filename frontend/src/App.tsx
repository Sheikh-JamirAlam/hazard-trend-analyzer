import { lazy, Suspense, useState } from "react";
import type { FormEvent } from "react";
import { ArrowDownRight, ArrowUpRight, Database, MapPin, Sun, Activity, CalendarDays, Crosshair, Radio, RotateCcw } from "lucide-react";
import { fetchHeatwaveAnalysis } from "./api";
import type { HeatwaveAnalysis } from "./api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";

const AnnualChart = lazy(() => import("./AnnualChart").then((module) => ({ default: module.AnnualChart })));

const places = [
  { name: "Delhi, India", latitude: "28.6139", longitude: "77.2090" },
  { name: "Kolkata, India", latitude: "22.5726", longitude: "88.3639" },
  { name: "Mumbai, India", latitude: "19.0760", longitude: "72.8777" },
  { name: "Pune, India", latitude: "18.5204", longitude: "73.8567" },
  { name: "Dubai, United Arab Emirates", latitude: "25.2048", longitude: "55.2708" },
  { name: "Phoenix, United States", latitude: "33.4484", longitude: "-112.0740" },
  { name: "Sydney, Australia", latitude: "-33.8688", longitude: "151.2093" },
  { name: "Madrid, Spain", latitude: "40.4168", longitude: "-3.7038" },
  { name: "Rome, Italy", latitude: "41.9028", longitude: "12.4964" },
  { name: "Buenos Aires, Argentina", latitude: "-34.6037", longitude: "-58.3816" },
];

const labelClass = "mb-2 block font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[#565650]";
const inputClass = "h-12 w-full border-2 border-[#171714] bg-[#f4f4f0] px-3 font-mono text-sm font-bold tabular-nums text-[#111] outline-none transition-colors focus:border-[#e61919] focus:bg-white";

function App() {
  const [place, setPlace] = useState(places[0]);
  const [startYear, setStartYear] = useState("2010");
  const [endYear, setEndYear] = useState("2024");
  const [result, setResult] = useState<HeatwaveAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runAnalysis() {
    const firstYear = Number(startYear);
    const lastYear = Number(endYear);
    const latitude = Number(place.latitude);
    const longitude = Number(place.longitude);
    if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
      setError("Latitude must be between −90 and 90 degrees.");
      return;
    }
    if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
      setError("Longitude must be between −180 and 180 degrees.");
      return;
    }
    if (!Number.isInteger(firstYear) || !Number.isInteger(lastYear) || firstYear < 1940 || firstYear > lastYear || lastYear > new Date().getFullYear()) {
      setError("Choose a valid year range from 1940 through the current year.");
      return;
    }
    if (lastYear - firstYear + 1 > 40) {
      setError("The selected period can be up to 40 years.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const analysis = await fetchHeatwaveAnalysis({
        latitude,
        longitude,
        startYear: firstYear,
        endYear: lastYear,
        locationLabel: place.name,
      });
      setResult(analysis);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The analysis could not be completed.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runAnalysis();
  }

  const trendLabel =
    result?.insight.trend_direction === "unavailable"
      ? "Not enough data"
      : result?.insight.trend_direction
        ? `${result.insight.trend_direction[0].toUpperCase()}${result.insight.trend_direction.slice(1)}`
        : "Awaiting analysis";

  return (
    <main className="min-h-screen bg-[#eae8e3] text-[#111] selection:bg-[#e61919] selection:text-white">
      <header className="mx-auto flex max-w-[1440px] items-center justify-between border-b-2 border-[#171714] px-5 py-4 md:px-10">
        <a className="flex items-center gap-3 font-mono text-sm font-black uppercase tracking-[-0.04em]" href="#top" aria-label="Thermal Atlas home">
          <span className="grid size-9 place-items-center bg-[#e61919] text-white">
            <Sun size={21} strokeWidth={2.5} />
          </span>
          <span>
            THERMAL<span className="text-[#e61919]">/</span>ATLAS
          </span>
        </a>
        <div className="hidden items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em] sm:flex">
          <span className="size-2 bg-[#e61919]" /> Historical climate indicators
        </div>
        <a className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.12em] underline decoration-2 underline-offset-4 hover:text-[#e61919]" href="#method">
          Methodology <ArrowUpRight size={13} />
        </a>
      </header>

      <div className="mx-auto max-w-[1440px] px-5 md:px-10">
        <section id="top" className="grid gap-8 border-b-2 border-[#171714] py-10 md:grid-cols-[1.2fr_0.8fr] md:items-end md:gap-12 md:py-16">
          <div>
            <div className="mb-5 flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#55554e]">
              <span className="bg-[#171714] px-2 py-1 text-white">01</span> / Regional analysis
            </div>
            <h1 className="max-w-4xl text-[clamp(3.5rem,9vw,8.5rem)] font-black uppercase leading-[0.83] tracking-[-0.075em]">
              Heat leaves
              <br />
              <span className="text-[#e61919]">a record.</span>
            </h1>
            <p className="mt-7 max-w-xl text-base leading-relaxed text-[#45453f] md:text-lg">
              Track persistent high temperatures through time. Every signal is grounded in historical daily temperature observations.
            </p>
          </div>
          <aside className="relative border-2 border-[#171714] bg-[#f4f4f0] p-5 md:p-7">
            <span className="absolute -top-3 left-4 bg-[#eae8e3] px-2 font-mono text-[10px] font-bold uppercase tracking-[0.15em]">Definition / A-01</span>
            <div className="mb-5 flex items-center gap-3">
              <Sun className="text-[#e61919]" size={24} />
              <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em]">Working threshold</span>
            </div>
            <p className="max-w-md text-lg font-semibold leading-snug md:text-xl">
              Three or more consecutive days above the local <span className="underline decoration-4 decoration-[#e61919] underline-offset-2">95th percentile</span> of daily maximum temperature.
            </p>
            <div className="mt-6 flex items-center justify-between border-t border-[#171714] pt-3 font-mono text-[9px] uppercase tracking-[0.12em] text-[#55554e]">
              <span>Heatwave event rule</span>
              <span>THR / 095</span>
            </div>
          </aside>
        </section>

        <section className="grid gap-8 py-8 lg:grid-cols-[330px_1fr] lg:gap-10 lg:py-10" aria-label="Heatwave analysis workspace">
          <form onSubmit={handleSubmit} className="self-start border-2 border-[#171714] bg-[#f4f4f0]">
            <div className="flex items-start justify-between border-b-2 border-[#171714] bg-[#171714] px-5 py-4 text-white">
              <div>
                <span className="font-mono text-[9px] font-bold uppercase tracking-[0.18em] text-[#c6c6bd]">Define your window</span>
                <h2 className="mt-1 text-2xl font-black uppercase leading-none tracking-[-0.05em]">Set coordinates</h2>
              </div>
              <span className="border border-white/50 px-2 py-1 font-mono text-[9px] font-bold tracking-widest">01—03</span>
            </div>
            <div className="space-y-5 p-5">
              <div>
                <label className={labelClass} htmlFor="location-trigger">
                  Location / Preset
                </label>
                <div className="relative">
                  <MapPin className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-[#e61919]" size={16} />
                  <Select
                    value={place.name}
                    onValueChange={(value) => {
                      const selected = places.find((item) => item.name === value);
                      if (selected) setPlace(selected);
                    }}
                  >
                    <SelectTrigger
                      id="location-trigger"
                      className="h-12 w-full rounded-none border-2 border-[#171714] bg-[#f4f4f0] pl-10 pr-3 font-mono text-xs font-bold uppercase tracking-wide text-[#111] shadow-none focus-visible:border-[#e61919] focus-visible:ring-0 data-popup-open:border-[#e61919]"
                    >
                      <SelectValue placeholder="Select a region" />
                    </SelectTrigger>
                    <SelectContent align="start" className="rounded-none border-2 border-[#171714] bg-[#f4f4f0] p-1 font-mono text-xs font-bold uppercase text-[#111] shadow-none">
                      {places.map((item) => (
                        <SelectItem key={item.name} value={item.name} className="rounded-none px-3 py-3 focus:bg-[#e61919] focus:text-white">
                          {item.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <label>
                  <span className={labelClass}>Latitude</span>
                  <span className="relative block">
                    <input
                      aria-label="Latitude"
                      className={`${inputClass} pr-10`}
                      type="number"
                      step="any"
                      min="-90"
                      max="90"
                      value={place.latitude}
                      onChange={(event) => setPlace({ ...place, name: "Custom coordinates", latitude: event.target.value })}
                    />
                    <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 font-mono text-[9px] uppercase text-[#77776e]">° N/S</span>
                  </span>
                </label>
                <label>
                  <span className={labelClass}>Longitude</span>
                  <span className="relative block">
                    <input
                      aria-label="Longitude"
                      className={`${inputClass} pr-10`}
                      type="number"
                      step="any"
                      min="-180"
                      max="180"
                      value={place.longitude}
                      onChange={(event) => setPlace({ ...place, name: "Custom coordinates", longitude: event.target.value })}
                    />
                    <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 font-mono text-[9px] uppercase text-[#77776e]">° E/W</span>
                  </span>
                </label>
              </div>

              <div>
                <label className={`${labelClass} flex items-center justify-between`}>
                  <span>Observation period</span>
                  <CalendarDays size={14} />
                </label>
                <div className="grid grid-cols-[1fr_auto_1fr] items-end gap-2 border-2 border-[#171714] p-3">
                  <label>
                    <span className="mb-1 block font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-[#77776e]">From</span>
                    <input
                      aria-label="Start year"
                      className="w-full bg-transparent font-mono text-lg font-black tabular-nums outline-none focus:text-[#e61919]"
                      type="number"
                      min="1940"
                      max={new Date().getFullYear()}
                      value={startYear}
                      onChange={(event) => setStartYear(event.target.value)}
                    />
                  </label>
                  <span className="pb-1 font-mono text-[#e61919]">/</span>
                  <label>
                    <span className="mb-1 block font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-[#77776e]">To</span>
                    <input
                      aria-label="End year"
                      className="w-full bg-transparent font-mono text-lg font-black tabular-nums outline-none focus:text-[#e61919]"
                      type="number"
                      min="1940"
                      max={new Date().getFullYear()}
                      value={endYear}
                      onChange={(event) => setEndYear(event.target.value)}
                    />
                  </label>
                </div>
                <p className="mt-2 font-mono text-[9px] uppercase leading-relaxed tracking-[0.06em] text-[#66665f]">■ Up to 40 years / Source records from 1940 onward</p>
              </div>

              <button
                className="group flex min-h-14 w-full items-center justify-between border-2 border-[#171714] bg-[#e61919] px-4 text-left font-mono text-xs font-black uppercase tracking-[0.08em] text-white transition-colors hover:bg-[#171714] disabled:cursor-wait disabled:bg-[#55554e]"
                type="submit"
                disabled={loading}
              >
                <span>{loading ? "Reading the record…" : "Analyze heatwave trend"}</span>
                <ArrowUpRight className="transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" size={19} />
              </button>
              {error && (
                <div className="border-2 border-[#e61919] bg-[#fff1ed] p-3 font-mono text-xs leading-relaxed text-[#8b1515]" role="alert">
                  <p className="font-bold uppercase">Error / Request not completed</p>
                  <p className="mt-1">{error}</p>
                  <button
                    type="button"
                    className="mt-3 inline-flex items-center gap-2 border border-[#8b1515] px-2 py-1 font-bold uppercase hover:bg-[#e61919] hover:text-white"
                    onClick={() => void runAnalysis()}
                  >
                    <RotateCcw size={12} /> Retry
                  </button>
                </div>
              )}
            </div>
            <div className="flex items-center justify-between border-t-2 border-[#171714] px-5 py-3 font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#68685f]">
              <span>Input system / live</span>
              <Crosshair size={14} />
            </div>
          </form>

          <div className="min-w-0" aria-live="polite">
            {!result && !loading && (
              <div className="flex min-h-[460px] flex-col justify-between border-2 border-[#171714] bg-[#f4f4f0]">
                <div className="flex items-center justify-between border-b-2 border-[#171714] px-5 py-3 font-mono text-[9px] font-bold uppercase tracking-[0.15em]">
                  <span>Output bay / 00</span>
                  <span className="text-[#e61919]">NO DATA LOADED</span>
                </div>
                <div className="relative flex flex-1 flex-col justify-center overflow-hidden px-6 py-12 md:px-12">
                  <div className="pointer-events-none absolute right-4 top-4 font-mono text-[8px] leading-tight tracking-[0.24em] text-[#c5c3bb]">
                    + + + + + +<br />+ + + + + +<br />+ + + + + +
                  </div>
                  <div className="mb-8 flex size-16 items-center justify-center border-2 border-[#171714] bg-[#e61919] text-white">
                    <Activity size={30} />
                  </div>
                  <span className="mb-3 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#62625b]">System idle / awaiting input</span>
                  <h2 className="max-w-2xl text-5xl font-black uppercase leading-[0.87] tracking-[-0.07em] md:text-7xl">
                    Your climate
                    <br />
                    <span className="text-[#e61919]">record, in context.</span>
                  </h2>
                  <p className="mt-6 max-w-lg leading-relaxed text-[#55554e]">
                    Choose a location and period to reveal the annual pattern. Summary, chart, and interpretation will use the same analyzed observations.
                  </p>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-[#171714] px-5 py-3 font-mono text-[9px] font-bold uppercase tracking-[0.1em]">
                  <span>/// Ready for analysis request</span>
                  <span>Ref / THA-001</span>
                </div>
              </div>
            )}

            {loading && (
              <div className="flex min-h-[460px] flex-col justify-between border-2 border-[#171714] bg-[#171714] p-6 text-[#f4f4f0] md:p-10" aria-label="Analysis loading">
                <div className="flex items-center gap-3 font-mono text-xs font-bold uppercase tracking-[0.14em]">
                  <Radio className="animate-pulse text-[#e61919]" size={18} /> Connecting to climate archive
                </div>
                <div>
                  <div className="mb-5 h-2 w-full border border-[#f4f4f0]/40">
                    <div className="h-full w-2/3 animate-pulse bg-[#e61919]" />
                  </div>
                  <h2 className="text-4xl font-black uppercase leading-none tracking-[-0.06em] md:text-6xl">
                    Reading
                    <br />
                    the record<span className="text-[#e61919]">...</span>
                  </h2>
                  <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.12em] text-[#c6c6bd]">Fetching and analyzing historical daily observations</p>
                </div>
                <span className="font-mono text-[9px] uppercase tracking-[0.14em]">Telemetry / in progress</span>
              </div>
            )}

            {result && !loading && (
              <>
                <div className="mb-5 flex flex-col justify-between gap-4 border-b-2 border-[#171714] pb-4 md:flex-row md:items-end">
                  <div>
                    <span className="mb-2 block font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[#62625b]">
                      Analysis / {result.period.start_year}—{result.period.end_year}
                    </span>
                    <h2 className="text-4xl font-black uppercase leading-none tracking-[-0.06em] md:text-6xl">
                      {result.location.label || `${result.location.latitude.toFixed(2)}°, ${result.location.longitude.toFixed(2)}°`}
                    </h2>
                  </div>
                  <span className="inline-flex items-center gap-2 self-start border-2 border-[#171714] px-3 py-2 font-mono text-[9px] font-bold uppercase tracking-[0.1em] md:self-auto">
                    <span className="size-2 bg-[#e61919]" />
                    {result.cache.hit ? "Cached result" : "Live analysis"}
                    {result.cache.generated_at ? ` / ${new Date(result.cache.generated_at).toLocaleDateString()}` : ""}
                  </span>
                </div>

                <div className="mb-6 grid grid-cols-1 border-2 border-[#171714] bg-[#171714] gap-px sm:grid-cols-2 xl:grid-cols-4">
                  <article className="min-h-40 bg-[#e61919] p-4 text-white">
                    <div className="flex items-center justify-between font-mono text-[9px] font-bold uppercase tracking-[0.13em]">
                      <span>Events detected</span>
                      <Sun size={16} />
                    </div>
                    <data className="mt-5 block text-6xl font-black leading-none tracking-[-0.07em]">{result.total_events}</data>
                    <small className="mt-3 block font-mono text-[9px] uppercase tracking-wide">
                      Heatwave events / {result.period.start_year}–{result.period.end_year}
                    </small>
                  </article>
                  <Metric title="Mean duration" unit="Days" value={result.summary.mean_event_duration_days?.toFixed(1) ?? "—"} caption="Per detected event" />
                  <Metric title="Mean intensity" unit="°C above" value={result.summary.mean_event_intensity_celsius?.toFixed(1) ?? "—"} caption="Mean excess during events" />
                  <article className="min-h-40 bg-[#f4f4f0] p-4">
                    <div className="flex items-center justify-between font-mono text-[9px] font-bold uppercase tracking-[0.13em]">
                      <span>Linear trend</span>
                      {result.insight.trend_slope_events_per_year !== null && result.insight.trend_slope_events_per_year > 0 ? (
                        <ArrowUpRight size={16} className="text-[#e61919]" />
                      ) : (
                        <ArrowDownRight size={16} />
                      )}
                    </div>
                    <data className="mt-5 block text-3xl font-black uppercase leading-none tracking-[-0.06em]">{trendLabel}</data>
                    <small className="mt-3 block font-mono text-[9px] uppercase tracking-wide text-[#62625b]">
                      {result.insight.trend_slope_events_per_year === null
                        ? "Not estimated"
                        : `${result.insight.trend_slope_events_per_year > 0 ? "+" : ""}${result.insight.trend_slope_events_per_year.toFixed(2)} events / year`}
                    </small>
                  </article>
                </div>

                <section className="mb-6 border-2 border-[#171714] bg-[#f4f4f0]">
                  <div className="flex flex-col justify-between gap-3 border-b-2 border-[#171714] px-4 py-4 sm:flex-row sm:items-end">
                    <div>
                      <span className="font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-[#62625b]">Year by year / annual series</span>
                      <h3 className="mt-1 text-2xl font-black uppercase leading-none tracking-[-0.05em]">Heatwave frequency</h3>
                    </div>
                    <span className="font-mono text-[9px] font-bold uppercase tracking-[0.1em]">
                      <i className="mr-2 inline-block size-2 bg-[#e61919]" />
                      Events per year
                    </span>
                  </div>
                  <div className="h-[300px] p-3 sm:h-[360px] sm:p-5">
                    <Suspense fallback={<div className="grid h-full place-items-center font-mono text-xs uppercase">Loading chart…</div>}>
                      <AnnualChart data={result.annual_metrics} />
                    </Suspense>
                  </div>
                  <div className="flex justify-between gap-3 border-t border-[#171714] px-4 py-2 font-mono text-[8px] font-bold uppercase tracking-[0.12em] text-[#62625b]">
                    <span>Years with missing data are left open</span>
                    <span>Events / year</span>
                  </div>
                </section>

                <section className="mb-6 grid gap-4 border-2 border-[#171714] bg-[#171714] p-5 text-[#f4f4f0] md:grid-cols-[52px_1fr] md:p-6">
                  <div className="grid size-12 place-items-center bg-[#e61919] text-white">
                    <Activity size={24} />
                  </div>
                  <div>
                    <span className="font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-[#c6c6bd]">Computed insight / descriptive only</span>
                    <p className="mt-2 text-lg font-semibold leading-relaxed md:text-xl">{result.insight.text}</p>
                    <span className="mt-3 block font-mono text-[9px] uppercase tracking-[0.1em] text-[#c6c6bd]">Trend does not establish causation</span>
                  </div>
                </section>

                <details className="border-2 border-[#171714] bg-[#f4f4f0]">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-4 font-mono text-[10px] font-bold uppercase tracking-[0.12em] marker:content-none hover:bg-[#e1dfd8]">
                    <span className="flex items-center gap-3">
                      <Database className="text-[#e61919]" size={17} /> Data quality / assumptions
                    </span>
                    <span className="text-lg">＋</span>
                  </summary>
                  <div className="border-t-2 border-[#171714] p-4">
                    <div className="grid gap-px border-2 border-[#171714] bg-[#171714] sm:grid-cols-2 xl:grid-cols-4">
                      <Quality label="Observed days" value={result.data_quality.observed_days.toLocaleString()} />
                      <Quality label="Missing / null" value={result.data_quality.missing_days.toLocaleString()} />
                      <Quality label="Baseline / coverage" value={`${result.baseline.start_year}–${result.baseline.end_year} / ${result.baseline.coverage_percent}%`} />
                      <Quality label="Threshold" value={`${result.threshold_celsius.toFixed(1)}°C`} />
                    </div>
                    <ul className="mt-4 list-square space-y-2 pl-5 text-sm leading-relaxed text-[#45453f]">
                      {result.caveats.map((caveat) => (
                        <li key={caveat}>{caveat}</li>
                      ))}
                    </ul>
                    <p className="mt-4 border-t border-[#171714] pt-3 font-mono text-[9px] uppercase leading-relaxed tracking-[0.05em] text-[#62625b]">
                      Dataset: {result.data_source.model} / {result.data_source.variable} / {result.data_source.unit}. Source:{" "}
                      <a className="font-bold text-[#e61919] underline underline-offset-2" href="https://open-meteo.com/" target="_blank" rel="noreferrer">
                        {result.data_source.name}
                      </a>
                      .
                    </p>
                  </div>
                </details>
              </>
            )}
          </div>
        </section>

        <footer
          id="method"
          className="flex flex-col justify-between gap-3 border-t-2 border-[#171714] py-5 font-mono text-[9px] font-bold uppercase leading-relaxed tracking-[0.09em] text-[#62625b] md:flex-row"
        >
          <span>
            Thermal Atlas <i className="text-[#e61919]">/</i> Historical heatwave indicators
          </span>
          <span>
            Weather data ©{" "}
            <a className="text-[#111] underline" href="https://open-meteo.com/" target="_blank" rel="noreferrer">
              Open-Meteo.com
            </a>{" "}
            <i className="text-[#e61919]">/</i> Percentile trends do not attribute cause.
          </span>
        </footer>
      </div>
    </main>
  );
}

function Metric({ title, unit, value, caption }: { title: string; unit: string; value: string; caption: string }) {
  return (
    <article className="min-h-40 bg-[#f4f4f0] p-4">
      <div className="flex items-center justify-between font-mono text-[9px] font-bold uppercase tracking-[0.13em]">
        <span>{title}</span>
        <span className="text-[#77776e]">{unit}</span>
      </div>
      <data className="mt-5 block text-6xl font-black leading-none tracking-[-0.07em]">{value}</data>
      <small className="mt-3 block font-mono text-[9px] uppercase tracking-wide text-[#62625b]">{caption}</small>
    </article>
  );
}

function Quality({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#f4f4f0] p-3">
      <span className="block font-mono text-[8px] font-bold uppercase tracking-[0.1em] text-[#62625b]">{label}</span>
      <b className="mt-2 block font-mono text-sm tabular-nums">{value}</b>
    </div>
  );
}

export default App;
