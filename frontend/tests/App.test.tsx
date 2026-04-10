import { render, screen, userEvent } from "../src/test/test-utils";
import App from "../src/app/App";

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

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/health")) {
          return jsonResponse({ status: "ok" });
        }
        if (url.endsWith("/samples")) {
          return jsonResponse([]);
        }
        return jsonResponse({ detail: "Not found" }, false);
      }),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders workspace headings", async () => {
    render(<App />);
    expect(await screen.findByText("AI Call Center Assistant")).toBeInTheDocument();
    expect(screen.getByText("Call Review Workspace")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyze call" })).toBeInTheDocument();
  });

  it("analyzes transcript input and renders summary content", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/health")) {
          return jsonResponse({ status: "ok" });
        }
        if (url.endsWith("/samples")) {
          return jsonResponse([]);
        }
        if (url.endsWith("/analyze/text")) {
          return jsonResponse({
            metadata: { call_id: "CALL-1001", input_type: "transcript", duration_estimate: "03:30" },
            transcript: "Agent: Hello. Customer: I need a refund.",
            summary: {
              one_line_summary: "Customer asked for a billing refund and the agent resolved it.",
              customer_issue: "Unexpected billing charge",
              resolution: "Refund processed",
              action_items: ["Send refund confirmation email"],
              key_topics: ["billing", "refund"],
              sentiment: "Neutral",
              call_outcome: "Resolved",
            },
            qa_score: {
              empathy: { score: 8, justification: "Acknowledged frustration." },
              professionalism: { score: 9, justification: "Clear and respectful tone." },
              resolution: { score: 9, justification: "Issue resolved within call." },
              communication_clarity: { score: 8, justification: "Next steps explained." },
              overall_score: 9,
              grade: "Excellent",
              highlights: ["Clear ownership of issue"],
              improvements: ["Confirm follow-up timeline earlier"],
            },
            current_stage: "complete",
            errors: [],
            fallback_used: false,
          });
        }
        return jsonResponse({ detail: "Not found" }, false);
      }),
    );

    render(<App />);

    const transcriptInput = screen.getByPlaceholderText(
      "Agent: Thank you for calling. Customer: I need help with my billing issue.",
    );
    await userEvent.type(transcriptInput, "Agent: Hello. Customer: I need help with a refund.");
    await userEvent.click(screen.getByRole("button", { name: "Analyze call" }));

    expect(await screen.findByText("Customer asked for a billing refund and the agent resolved it.")).toBeInTheDocument();
    expect(screen.getByText("Refund processed")).toBeInTheDocument();
    expect(screen.getByText("Resolved")).toBeInTheDocument();
  });
});
