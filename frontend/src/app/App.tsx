import { useEffect, useState } from "react";

import { Sidebar } from "./components/Sidebar";
import { InputPanel } from "./components/InputPanel";
import { RunStatusPanel } from "./components/RunStatusPanel";
import { ResultTabs } from "./components/ResultTabs";
import {
  analyzeAudio,
  analyzeJson,
  analyzeTranscript,
  fetchSampleTranscript,
  fetchSamples,
  healthcheck,
} from "../services/api";
import type { AnalysisResult, InputMode, ResultTab, SampleItem } from "../shared/types";

const HISTORY_LIMIT = 20;

export default function App() {
  const [apiStatus, setApiStatus] = useState<"checking" | "ready" | "offline">("checking");
  const [inputError, setInputError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [sampleMessage, setSampleMessage] = useState("");
  const [samplesLoading, setSamplesLoading] = useState(false);
  const [inputMode, setInputMode] = useState<InputMode>("transcript");
  const [activeTab, setActiveTab] = useState<ResultTab>("summary");
  const [samples, setSamples] = useState<SampleItem[]>([]);
  const [selectedSample, setSelectedSample] = useState("");
  const [transcriptText, setTranscriptText] = useState("");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [jsonFileName, setJsonFileName] = useState("transcript.json");
  const [jsonText, setJsonText] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>([]);
  const [busy, setBusy] = useState(false);

  const loadSamples = () => {
    setSampleMessage("");
    setSamplesLoading(true);
    fetchSamples()
      .then((items) => {
        setSamples(items);
        if (!items.length) setSampleMessage("No sample transcripts found on the server.");
      })
      .catch((error) => {
        setSamples([]);
        setSampleMessage(error instanceof Error ? error.message : "Unable to load samples.");
      })
      .finally(() => setSamplesLoading(false));
  };

  useEffect(() => {
    healthcheck()
      .then(() => setApiStatus("ready"))
      .catch(() => setApiStatus("offline"));
    loadSamples();
  }, []);

  // Race-safe sample fetch: cancel stale responses if user switches quickly.
  useEffect(() => {
    if (!selectedSample) return;
    let cancelled = false;
    fetchSampleTranscript(selectedSample)
      .then((sample) => {
        if (cancelled) return;
        setTranscriptText(sample.transcript);
        setInputMode("transcript");
      })
      .catch((error) => {
        if (cancelled) return;
        setInputError(error instanceof Error ? error.message : "Unable to load sample.");
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSample]);

  const onJsonFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = await file.text();
      JSON.parse(content);
      setJsonFileName(file.name);
      setJsonText(content);
      setInputError("");
    } catch {
      setInputError("Invalid JSON file. Please upload a valid .json transcript.");
    } finally {
      event.target.value = "";
    }
  };

  const clearResults = () => {
    setResult(null);
    setHistory([]);
    setInputError("");
    setSuccessMessage("");
    setActiveTab("summary");
  };

  const runAnalysis = async () => {
    setBusy(true);
    setInputError("");
    setSuccessMessage("");
    try {
      let nextResult: AnalysisResult;
      if (inputMode === "transcript") {
        nextResult = await analyzeTranscript(transcriptText);
      } else if (inputMode === "json") {
        let payload: object;
        try {
          payload = JSON.parse(jsonText);
        } catch {
          throw new Error("JSON content is invalid. Please fix it before analyzing.");
        }
        nextResult = await analyzeJson(payload, jsonFileName);
      } else {
        if (!audioFile) throw new Error("Upload an audio file before analyzing.");
        nextResult = await analyzeAudio(audioFile);
      }
      setResult(nextResult);
      setHistory((current) => [...current, nextResult].slice(-HISTORY_LIMIT));
      setActiveTab("summary");
      const grade = nextResult.qa_score?.grade;
      setSuccessMessage(grade ? `Analysis complete — Grade: ${grade}` : "Analysis complete.");
    } catch (error) {
      setInputError(error instanceof Error ? error.message : "Analysis failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="shell">
      <Sidebar
        apiStatus={apiStatus}
        samples={samples}
        samplesLoading={samplesLoading}
        selectedSample={selectedSample}
        onSelectSample={setSelectedSample}
        sampleMessage={sampleMessage}
        onReloadSamples={loadSamples}
        onClearResults={clearResults}
      />

      <main className="main">
        <header className="hero">
          <div>
            <p className="eyebrow">Call Review Workspace</p>
            <h2>Upload a call, inspect the transcript, and review the outcome in one pass.</h2>
          </div>
        </header>

        <section className="workspace two-column">
          <InputPanel
            inputMode={inputMode}
            onInputModeChange={setInputMode}
            busy={busy}
            onAnalyze={runAnalysis}
            transcriptText={transcriptText}
            onTranscriptChange={setTranscriptText}
            audioFile={audioFile}
            onAudioChange={setAudioFile}
            jsonText={jsonText}
            jsonFileName={jsonFileName}
            onJsonTextChange={setJsonText}
            onJsonFileNameChange={setJsonFileName}
            onJsonFileChange={onJsonFileChange}
            inlineError={inputError}
            inlineSuccess={successMessage}
          />
          <RunStatusPanel result={result} />
        </section>

        <ResultTabs activeTab={activeTab} onTabChange={setActiveTab} result={result} history={history} />
      </main>
    </div>
  );
}
