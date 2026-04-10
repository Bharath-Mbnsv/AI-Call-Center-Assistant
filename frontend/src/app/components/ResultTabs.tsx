import { useMemo } from "react";

import { resultTabs } from "../constants";
import type { AnalysisResult, ResultTab } from "../../shared/types";

type Props = {
  activeTab: ResultTab;
  onTabChange: (tab: ResultTab) => void;
  result: AnalysisResult | null;
  history: AnalysisResult[];
};

export function ResultTabs({ activeTab, onTabChange, result, history }: Props) {
  const summary = result?.summary;
  const qa = result?.qa_score;
  const metadata = result?.metadata as Record<string, unknown> | undefined;

  const metrics = useMemo(() => {
    if (!qa || qa.error) return [];
    return [
      { label: "Empathy", value: qa.empathy?.score ?? "N/A" },
      { label: "Professionalism", value: qa.professionalism?.score ?? "N/A" },
      { label: "Resolution", value: qa.resolution?.score ?? "N/A" },
      { label: "Clarity", value: qa.communication_clarity?.score ?? "N/A" },
    ];
  }, [qa]);

  const historyScores = useMemo(
    () =>
      history
        .map((entry, index) => ({
          label: `Run ${index + 1}`,
          score: entry.qa_score?.overall_score ?? null,
        }))
        .filter((item): item is { label: string; score: number } => typeof item.score === "number"),
    [history],
  );

  return (
    <section className="panel">
      <nav className="tabs" role="tablist" aria-label="Result views">
        {resultTabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.key}
            className={activeTab === tab.key ? "active" : ""}
            onClick={() => onTabChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {!result ? <p className="empty-copy">Run an analysis to view summary, QA, transcript, and session history.</p> : null}

      {result && activeTab === "summary" ? (
        <SummaryView summary={summary} metadata={metadata} />
      ) : null}

      {result && activeTab === "qa" ? <QAView qa={qa} metrics={metrics} /> : null}

      {result && activeTab === "transcript" ? (
        <article className="card-block">
          <h3>Transcript</h3>
          <pre>{result.transcript ?? "No transcript available."}</pre>
        </article>
      ) : null}

      {activeTab === "history" ? (
        history.length ? (
          <HistoryView history={history} historyScores={historyScores} />
        ) : (
          <p className="empty-copy">Run multiple analyses to build session history.</p>
        )
      ) : null}
    </section>
  );
}

// ── Sub-views ────────────────────────────────────────────────────────

function SummaryView({
  summary,
  metadata,
}: {
  summary: AnalysisResult["summary"];
  metadata: Record<string, unknown> | undefined;
}) {
  return (
    <div className="stack">
      <div className="metrics-grid">
        <article className="metric-card">
          <span>Call ID</span>
          <strong>{String(metadata?.call_id ?? "N/A").slice(-8)}</strong>
        </article>
        <article className="metric-card">
          <span>Input Type</span>
          <strong>{String(metadata?.input_type ?? "N/A")}</strong>
        </article>
        <article className="metric-card">
          <span>Duration</span>
          <strong>{String(metadata?.duration_estimate ?? "N/A")}</strong>
        </article>
        <article className="metric-card">
          <span>Outcome</span>
          <strong>{summary?.call_outcome ?? "N/A"}</strong>
        </article>
      </div>
      <article className="card-block">
        <h3>One-Line Summary</h3>
        <p>{summary?.one_line_summary ?? "N/A"}</p>
      </article>
      <article className="card-block">
        <h3>Customer Issue</h3>
        <p>{summary?.customer_issue ?? "N/A"}</p>
      </article>
      <article className="card-block">
        <h3>Resolution</h3>
        <p>{summary?.resolution ?? "N/A"}</p>
      </article>
      <article className="card-block">
        <h3>Key Topics</h3>
        <div className="tag-row">
          {(summary?.key_topics ?? []).map((topic) => (
            <span key={topic} className="tag">
              {topic}
            </span>
          ))}
        </div>
      </article>
      <article className="card-block">
        <h3>Action Items</h3>
        {(summary?.action_items ?? []).length ? (
          <ul className="plain-list">
            {summary?.action_items?.map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : (
          <p>No action items required.</p>
        )}
      </article>
    </div>
  );
}

function QAView({
  qa,
  metrics,
}: {
  qa: AnalysisResult["qa_score"];
  metrics: Array<{ label: string; value: number | string }>;
}) {
  return (
    <div className="stack">
      <div className="metrics-grid">
        <article className="metric-card">
          <span>Overall Score</span>
          <strong>{qa?.overall_score ?? "N/A"}</strong>
        </article>
        <article className="metric-card">
          <span>Grade</span>
          <strong>{qa?.grade ?? "N/A"}</strong>
        </article>
      </div>
      <div className="metrics-grid">
        {metrics.map((metric) => (
          <article key={metric.label} className="metric-card">
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </div>
      <article className="card-block">
        <h3>Highlights</h3>
        <ul className="plain-list">
          {(qa?.highlights ?? []).map((item) => <li key={item}>{item}</li>)}
        </ul>
      </article>
      <article className="card-block">
        <h3>Improvements</h3>
        <ul className="plain-list">
          {(qa?.improvements ?? []).map((item) => <li key={item}>{item}</li>)}
        </ul>
      </article>
    </div>
  );
}

function HistoryView({
  history,
  historyScores,
}: {
  history: AnalysisResult[];
  historyScores: Array<{ label: string; score: number }>;
}) {
  return (
    <div className="history-list">
      {historyScores.length ? (
        <article className="card-block history-chart-card">
          <div className="section-head">
            <h3>QA Score Trend</h3>
            <span className="pill">1-10 scale</span>
          </div>
          <svg viewBox="0 0 320 130" className="history-chart" role="img" aria-label="QA score trend chart">
            <line x1="20" y1="110" x2="300" y2="110" className="chart-axis" />
            <line x1="20" y1="20" x2="20" y2="110" className="chart-axis" />
            {historyScores.map((item, index) => {
              const x = historyScores.length === 1 ? 160 : 20 + (index * 280) / (historyScores.length - 1);
              const y = 110 - item.score * 9;
              return (
                <g key={`${item.label}-${index}`}>
                  <circle cx={x} cy={y} r="4" className="chart-dot" />
                  <text x={x} y={124} textAnchor="middle" className="chart-label">
                    {index + 1}
                  </text>
                </g>
              );
            })}
            <polyline
              className="chart-line"
              points={historyScores
                .map((item, index) => {
                  const x = historyScores.length === 1 ? 160 : 20 + (index * 280) / (historyScores.length - 1);
                  const y = 110 - item.score * 9;
                  return `${x},${y}`;
                })
                .join(" ")}
            />
          </svg>
          <p className="helper-text">Run order is shown on the x-axis. Higher points mean better QA score.</p>
        </article>
      ) : (
        <p className="helper-text">Score trend appears once runs include numeric QA scores.</p>
      )}
      {history.map((entry, index) => (
        <article key={`${(entry.metadata as Record<string, unknown> | undefined)?.call_id ?? "call"}-${index}`} className="card-block">
          <div className="section-head">
            <h3>{String((entry.metadata as Record<string, unknown> | undefined)?.call_id ?? `Run ${index + 1}`)}</h3>
            <span className="pill">{entry.qa_score?.grade ?? "No grade"}</span>
          </div>
          <p>{entry.summary?.one_line_summary ?? "No summary available."}</p>
        </article>
      ))}
    </div>
  );
}
