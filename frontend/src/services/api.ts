import type { AnalysisResult, SampleItem } from "../shared/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
const DEFAULT_TIMEOUT_MS = 120_000; // 2 min — audio transcription can take a while

async function request<T>(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${path}`, { ...init, signal: controller.signal });

    if (!response.ok) {
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const payload = await response.json();
        throw new Error(payload.detail || payload.message || `Request failed (${response.status})`);
      }
      throw new Error((await response.text()) || `Request failed (${response.status})`);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function healthcheck() {
  return request<{ status: "ok" }>("/health");
}

export function fetchSamples() {
  return request<SampleItem[]>("/samples");
}

export function fetchSampleTranscript(slug: string) {
  return request<{ slug: string; label: string; transcript: string }>(`/samples/${encodeURIComponent(slug)}`);
}

export function analyzeTranscript(transcript: string, filename = "transcript.txt") {
  return request<AnalysisResult>("/analyze/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript, filename }),
  });
}

export function analyzeJson(payload: object | Array<Record<string, unknown>>, filename = "transcript.json") {
  return request<AnalysisResult>("/analyze/json", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ payload, filename }),
  });
}

export function analyzeAudio(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<AnalysisResult>("/analyze/audio", {
    method: "POST",
    body: form,
  });
}
