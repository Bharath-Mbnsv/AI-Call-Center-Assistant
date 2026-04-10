import type { InputMode, ResultTab } from "../shared/types";

export const inputModes: Array<{ key: InputMode; label: string }> = [
  { key: "transcript", label: "Paste Transcript" },
  { key: "audio", label: "Upload Audio" },
  { key: "json", label: "Upload JSON Transcript" },
];

export const resultTabs: Array<{ key: ResultTab; label: string }> = [
  { key: "summary", label: "Summary" },
  { key: "qa", label: "Quality Score" },
  { key: "transcript", label: "Transcript" },
  { key: "history", label: "History" },
];
