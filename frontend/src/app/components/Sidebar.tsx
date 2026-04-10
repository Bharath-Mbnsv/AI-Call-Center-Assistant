import type { SampleItem } from "../../shared/types";

type ApiStatus = "checking" | "ready" | "offline";

type Props = {
  apiStatus: ApiStatus;
  samples: SampleItem[];
  samplesLoading: boolean;
  selectedSample: string;
  onSelectSample: (slug: string) => void;
  sampleMessage: string;
  onReloadSamples: () => void;
  onClearResults: () => void;
};

export function Sidebar({
  apiStatus,
  samples,
  samplesLoading,
  selectedSample,
  onSelectSample,
  sampleMessage,
  onReloadSamples,
  onClearResults,
}: Props) {
  const statusLabel = apiStatus === "ready" ? "Connected" : apiStatus === "offline" ? "Offline" : "Checking";

  return (
    <aside className="sidebar">
      <div>
        <p className="eyebrow">AI Call Center Assistant</p>
        <h1>Review calls without digging through long recordings.</h1>
        <p className="muted">
          Transcribe audio, summarize customer issues, and score agent performance in one workspace.
        </p>
      </div>

      <section className="panel">
        <div className="section-head">
          <h2>System</h2>
          <span className={`status ${apiStatus}`} aria-live="polite">
            {statusLabel}
          </span>
        </div>
        <p className="helper-text">
          Backend API status. Set the required API key on the server to run analyses.
        </p>
      </section>

      <section className="panel">
        <div className="section-head">
          <h2>Samples</h2>
        </div>
        <label className="visually-hidden" htmlFor="sample-select">
          Choose a sample transcript
        </label>
        <select
          id="sample-select"
          value={selectedSample}
          onChange={(event) => onSelectSample(event.target.value)}
          disabled={samplesLoading}
        >
          <option value="">{samplesLoading ? "Loading samples..." : "Choose a sample transcript"}</option>
          {samples.map((sample) => (
            <option key={sample.slug} value={sample.slug}>
              {sample.label}
            </option>
          ))}
        </select>
        {sampleMessage ? (
          <p className="helper-text">{sampleMessage}</p>
        ) : (
          <p className="helper-text">{samples.length} sample transcripts available.</p>
        )}
        <div className="sample-actions">
          <button className="ghost" type="button" onClick={onReloadSamples}>
            Reload samples
          </button>
          <button className="ghost" type="button" onClick={onClearResults}>
            Clear results
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>Pipeline</h2>
        <ul className="agent-list">
          <li>Intake validation and metadata extraction</li>
          <li>Whisper transcription for audio uploads</li>
          <li>Structured call summarization</li>
          <li>QA scoring across empathy, professionalism, resolution, and clarity</li>
        </ul>
      </section>
    </aside>
  );
}
