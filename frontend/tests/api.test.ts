import { analyzeTranscript, healthcheck } from "../src/services/api";

function jsonResponse(payload: unknown, ok = true): Response {
  return {
    ok,
    json: async () => payload,
    text: async () => JSON.stringify(payload),
    headers: {
      get: (name: string) => (name.toLowerCase() === "content-type" ? "application/json" : null),
    },
  } as unknown as Response;
}

describe("frontend api client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("calls health endpoint with an abort signal", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(healthcheck()).resolves.toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/health");
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });

  it("posts transcript payload for analysis", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ current_stage: "done" }));
    vi.stubGlobal("fetch", fetchMock);

    await analyzeTranscript("Agent: Hello. Customer: Hi.");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/analyze/text");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(typeof init.body).toBe("string");
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });

  it("surfaces structured error detail from non-ok JSON responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ detail: "Transcript too short" }, false));
    vi.stubGlobal("fetch", fetchMock);

    await expect(healthcheck()).rejects.toThrow("Transcript too short");
  });

  it("converts AbortError into a friendly timeout message", async () => {
    const fetchMock = vi.fn().mockImplementation(() => {
      const err = new DOMException("aborted", "AbortError");
      return Promise.reject(err);
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(healthcheck()).rejects.toThrow(/timed out/i);
  });
});
