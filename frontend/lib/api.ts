import { ChatResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type StreamHandlers = {
  onDelta: (delta: string) => void;
  onFinal: (response: ChatResponse) => void;
};

export async function streamChat(
  payload: Record<string, unknown>,
  handlers: StreamHandlers
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.body) {
    throw new Error("Streaming response body is unavailable.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.trim()) continue;
      const packet = JSON.parse(line) as
        | { type: "session"; session_id: string }
        | { type: "delta"; delta: string }
        | { type: "final"; response: ChatResponse };
      if (packet.type === "delta") handlers.onDelta(packet.delta);
      if (packet.type === "final") handlers.onFinal(packet.response);
    }
  }
}

