export type InputMode = "transcript" | "audio" | "json";
export type ResultTab = "summary" | "qa" | "transcript" | "history";

export type Summary = {
  one_line_summary?: string;
  customer_issue?: string;
  resolution?: string;
  action_items?: string[];
  key_topics?: string[];
  sentiment?: string;
  call_outcome?: string;
  error?: string | null;
};

export type DimensionScore = {
  score?: number | null;
  justification: string;
};

export type QAScore = {
  empathy: DimensionScore;
  professionalism: DimensionScore;
  resolution: DimensionScore;
  communication_clarity: DimensionScore;
  overall_score?: number | null;
  grade?: string | null;
  highlights: string[];
  improvements: string[];
  error?: string | null;
};

export type AnalysisResult = {
  metadata?: Record<string, unknown> | null;
  transcript?: string | null;
  summary?: Summary | null;
  qa_score?: QAScore | null;
  current_stage: string;
  errors: string[];
  fallback_used: boolean;
};

export type SampleItem = {
  slug: string;
  label: string;
};
