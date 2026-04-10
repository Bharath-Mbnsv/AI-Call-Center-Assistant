import type { AnalysisResult } from "../../shared/types";

type Props = {
  result: AnalysisResult | null;
};

export function RunStatusPanel({ result }: Props) {
  return (
    <div className="panel">
      <div className="section-head">
        <h2>Run Status</h2>
        <span className="pill">{result?.current_stage ?? "waiting"}</span>
      </div>
      <div className="stack">
        <div className="pipeline-step">1. Intake validation</div>
        <div className="pipeline-step">2. Transcription or text passthrough</div>
        <div className="pipeline-step">3. Structured summary</div>
        <div className="pipeline-step">4. QA scoring</div>
      </div>
      {result?.fallback_used ? <p className="error-copy">Fallback behavior was used during this run.</p> : null}
      {result?.errors?.length ? (
        <div className="stack">
          {result.errors.map((error, index) => (
            <p key={`${error}-${index}`} className="error-copy">
              {error}
            </p>
          ))}
        </div>
      ) : (
        <p className="helper-text">Errors and fallback notes will appear here when a stage needs recovery.</p>
      )}
    </div>
  );
}
