import { inputModes } from "../constants";
import type { InputMode } from "../../shared/types";

type Props = {
  inputMode: InputMode;
  onInputModeChange: (mode: InputMode) => void;
  busy: boolean;
  onAnalyze: () => void;

  transcriptText: string;
  onTranscriptChange: (value: string) => void;

  audioFile: File | null;
  onAudioChange: (file: File | null) => void;

  jsonText: string;
  jsonFileName: string;
  onJsonTextChange: (value: string) => void;
  onJsonFileNameChange: (value: string) => void;
  onJsonFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;

  inlineError?: string;
  inlineSuccess?: string;
};

export function InputPanel({
  inputMode,
  onInputModeChange,
  busy,
  onAnalyze,
  transcriptText,
  onTranscriptChange,
  audioFile,
  onAudioChange,
  jsonText,
  jsonFileName,
  onJsonTextChange,
  onJsonFileNameChange,
  onJsonFileChange,
  inlineError,
  inlineSuccess,
}: Props) {
  return (
    <div className="panel">
      <div className="section-head">
        <h2>Input</h2>
        <button className="primary" type="button" onClick={onAnalyze} disabled={busy}>
          {busy ? "Analyzing..." : "Analyze call"}
        </button>
      </div>

      <div className="tabs" role="tablist" aria-label="Input mode">
        {inputModes.map((mode) => (
          <button
            key={mode.key}
            type="button"
            role="tab"
            aria-selected={inputMode === mode.key}
            className={inputMode === mode.key ? "active" : ""}
            disabled={busy}
            onClick={() => onInputModeChange(mode.key)}
          >
            {mode.label}
          </button>
        ))}
      </div>

      {inlineError ? (
        <div className="flash error" role="alert">
          {inlineError}
        </div>
      ) : null}

      {!inlineError && inlineSuccess ? (
        <div className="flash success" role="status" aria-live="polite">
          {inlineSuccess}
        </div>
      ) : null}

      {inputMode === "transcript" ? (
        <div className="stack input-mode-card">
          <h3>Transcript Input</h3>
          <p className="helper-text">Paste the complete conversation with agent and customer turns.</p>
          <label className="visually-hidden" htmlFor="transcript-input">
            Transcript text
          </label>
          <textarea
            id="transcript-input"
            value={transcriptText}
            onChange={(event) => onTranscriptChange(event.target.value)}
            placeholder="Agent: Thank you for calling. Customer: I need help with my billing issue."
            rows={16}
            disabled={busy}
          />
        </div>
      ) : null}

      {inputMode === "audio" ? (
        <div className="stack input-mode-card">
          <h3>Audio Upload</h3>
          <p className="helper-text">Upload a call recording and we will transcribe it before scoring.</p>
          <label className="visually-hidden" htmlFor="audio-input">
            Audio file
          </label>
          <input
            id="audio-input"
            type="file"
            accept=".mp3,.mp4,.wav,.m4a,.webm,.ogg"
            onChange={(event) => onAudioChange(event.target.files?.[0] ?? null)}
            disabled={busy}
          />
          <p className="helper-text">
            {audioFile ? `${audioFile.name} selected` : "Upload an audio file to transcribe and analyze."}
          </p>
        </div>
      ) : null}

      {inputMode === "json" ? (
        <div className="stack input-mode-card">
          <h3>JSON Transcript</h3>
          <p className="helper-text">
            Use either <code>{"{\"transcript\":\"...\"}"}</code> or a speaker-turn array format.
          </p>
          <div className="json-tools">
            <label className="visually-hidden" htmlFor="json-file-input">
              JSON file
            </label>
            <input id="json-file-input" type="file" accept=".json,application/json" onChange={onJsonFileChange} disabled={busy} />
            <label className="visually-hidden" htmlFor="json-filename-input">
              JSON filename
            </label>
            <input
              id="json-filename-input"
              value={jsonFileName}
              onChange={(event) => onJsonFileNameChange(event.target.value)}
              placeholder="transcript.json"
              disabled={busy}
            />
          </div>
          <label className="visually-hidden" htmlFor="json-text-input">
            JSON content
          </label>
          <textarea
            id="json-text-input"
            value={jsonText}
            onChange={(event) => onJsonTextChange(event.target.value)}
            placeholder='{"transcript": "Agent: Hello..."}'
            rows={16}
            disabled={busy}
          />
        </div>
      ) : null}
    </div>
  );
}
