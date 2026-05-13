"use client";

import { FormEvent, useMemo, useState, useTransition } from "react";

import { streamChat } from "../lib/api";
import { ChatResponse, RetrievedSource } from "../lib/types";
import { SettingsPanel } from "./settings-panel";
import { SourceDrawer } from "./source-drawer";

type Message = {
  role: "user" | "assistant";
  content: string;
  safetyMode?: ChatResponse["safety_mode"];
  sources?: RetrievedSource[];
};

type Session = {
  id: string;
  title: string;
  messages: Message[];
};

const initialSession: Session = {
  id: "local-session",
  title: "New chat",
  messages: []
};

export function ChatApp() {
  const [sessions, setSessions] = useState<Session[]>([initialSession]);
  const [activeSessionId, setActiveSessionId] = useState(initialSession.id);
  const [input, setInput] = useState("");
  const [region, setRegion] = useState("US");
  const [privacyMode, setPrivacyMode] = useState(true);
  const [substanceHint, setSubstanceHint] = useState("general");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerSources, setDrawerSources] = useState<RetrievedSource[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isPending, startTransition] = useTransition();

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? sessions[0],
    [sessions, activeSessionId]
  );

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    const assistantPlaceholder: Message = { role: "assistant", content: "" };
    setInput("");

    setSessions((current) =>
      current.map((session) =>
        session.id === activeSessionId
          ? {
              ...session,
              title: session.messages.length ? session.title : trimmed.slice(0, 28),
              messages: [...session.messages, { role: "user", content: trimmed }, assistantPlaceholder]
            }
          : session
      )
    );

    setIsStreaming(true);
    try {
      await streamChat(
        {
          session_id: activeSessionId,
          user_message: trimmed,
          region,
          substance_hint: substanceHint,
          privacy_mode: privacyMode
        },
        {
          onDelta(delta) {
            setSessions((current) =>
              current.map((session) => {
                if (session.id !== activeSessionId) return session;
                const updated = [...session.messages];
                const last = updated[updated.length - 1];
                updated[updated.length - 1] = { ...last, content: `${last.content}${delta}` };
                return { ...session, messages: updated };
              })
            );
          },
          onFinal(response) {
            setSessions((current) =>
              current.map((session) => {
                if (session.id !== activeSessionId) return session;
                const updated = [...session.messages];
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: response.assistant_message,
                  safetyMode: response.safety_mode,
                  sources: response.retrieved_sources
                };
                return { ...session, messages: updated };
              })
            );
          }
        }
      );
    } finally {
      setIsStreaming(false);
    }
  }

  function createSession() {
    const id = `session-${Date.now()}`;
    startTransition(() => {
      setSessions((current) => [{ id, title: "New chat", messages: [] }, ...current]);
      setActiveSessionId(id);
    });
  }

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--text)]">
      <SettingsPanel
        open={settingsOpen}
        region={region}
        privacyMode={privacyMode}
        onClose={() => setSettingsOpen(false)}
        onRegionChange={setRegion}
        onPrivacyChange={setPrivacyMode}
      />
      <SourceDrawer open={drawerOpen} sources={drawerSources} onClose={() => setDrawerOpen(false)} />

      <div className="flex min-h-screen">
        <aside className="hidden w-72 shrink-0 border-r border-[var(--border)] bg-black p-3 md:flex md:flex-col">
          <div className="mb-4 flex items-center justify-between px-2 py-1">
            <div>
              <p className="text-xs font-medium uppercase text-[var(--muted)]">ChatSUD</p>
              <h1 className="text-base font-semibold">Recovery chat</h1>
            </div>
            <button
              className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--muted-strong)] transition hover:bg-[var(--surface-soft)]"
              onClick={createSession}
            >
              New
            </button>
          </div>

          <button
            className="mb-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-3 text-left text-sm text-[var(--muted-strong)] transition hover:bg-[var(--surface-soft)]"
            onClick={() => setSettingsOpen(true)}
          >
            Region: {region}
            <br />
            Privacy mode: {privacyMode ? "On" : "Off"}
          </button>

          <div className="space-y-1 overflow-y-auto">
            {sessions.map((session) => (
              <button
                key={session.id}
                className={`w-full rounded-lg px-3 py-3 text-left transition ${
                  session.id === activeSessionId
                    ? "bg-[var(--surface-soft)] text-[var(--text)]"
                    : "text-[var(--muted-strong)] hover:bg-[var(--surface)]"
                }`}
                onClick={() => setActiveSessionId(session.id)}
              >
                <p className="truncate text-sm font-medium">{session.title}</p>
                <p className="truncate text-xs opacity-75">
                  {session.messages.at(-1)?.content ?? "Start a new supportive conversation"}
                </p>
              </button>
            ))}
          </div>
        </aside>

        <section className="flex flex-1 flex-col bg-[var(--background)]">
          <header className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-4 py-3 md:px-5">
            <div>
              <p className="text-xs font-medium uppercase text-[var(--muted)]">Non-clinical support</p>
              <h2 className="text-base font-semibold md:text-lg">Safety-first recovery chat</h2>
            </div>
            <div className="flex items-center gap-2">
              <input
                className="w-32 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none transition focus:border-[var(--muted)] md:w-44"
                value={substanceHint}
                onChange={(event) => setSubstanceHint(event.target.value)}
                placeholder="Substance hint"
              />
              <button
                className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--muted-strong)] md:hidden"
                onClick={() => setSettingsOpen(true)}
              >
                Settings
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto py-6">
            {activeSession.messages.length === 0 ? (
              <div className="mx-auto flex min-h-[55vh] max-w-3xl flex-col items-start justify-center gap-5 px-5">
                <span className="rounded-md bg-[var(--accent-soft)] px-2.5 py-1 text-xs uppercase text-[var(--muted-strong)]">
                  Welcome
                </span>
                <h3 className="text-3xl font-semibold leading-tight text-[var(--text)] md:text-5xl">
                  A calmer, privacy-first space for recovery support.
                </h3>
                <p className="max-w-2xl text-base leading-7 text-[var(--muted)] md:text-lg">
                  ChatSUD offers supportive, non-clinical guidance grounded in indexed recovery materials.
                  It is not emergency care, diagnosis, or medical treatment.
                </p>
              </div>
            ) : (
              <div className="mx-auto flex max-w-3xl flex-col">
                {activeSession.messages.map((message, index) => (
                  <article
                    key={`${message.role}-${index}`}
                    className={`border-b border-[var(--border)] px-5 py-5 ${
                      message.role === "user" ? "bg-[var(--surface)]" : "bg-[var(--background)]"
                    }`}
                  >
                    <div className="flex gap-4">
                      <div
                        className={`mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold ${
                          message.role === "user"
                            ? "bg-[var(--accent)] text-black"
                            : "bg-[var(--surface-soft)] text-[var(--text)]"
                        }`}
                      >
                        {message.role === "user" ? "U" : "C"}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="whitespace-pre-wrap text-[15px] leading-7 text-[var(--text)]">
                          {message.content}
                        </p>
                        {message.safetyMode && message.safetyMode !== "supportive" ? (
                          <div className="mt-4 rounded-lg border border-[var(--danger)]/50 bg-[var(--danger)]/10 p-3 text-sm text-red-200">
                            Safety escalation engaged: {message.safetyMode.replace("_", " ")}
                          </div>
                        ) : null}
                        {message.sources?.length ? (
                          <div className="mt-4 flex flex-wrap gap-2">
                            {message.sources.map((source) => (
                              <button
                                key={`${source.source}-${source.title}`}
                                className="rounded-md border border-[var(--border)] px-2.5 py-1 text-xs text-[var(--muted-strong)] transition hover:bg-[var(--surface-soft)]"
                                onClick={() => {
                                  setDrawerSources(message.sources ?? []);
                                  setDrawerOpen(true);
                                }}
                              >
                                {source.title}
                              </button>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </article>
                ))}
                {isStreaming || isPending ? (
                  <div className="dot-wave mx-5 mt-4 w-fit rounded-lg bg-[var(--surface-raised)] px-4 py-3 text-sm text-[var(--muted)]">
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <form className="border-t border-[var(--border)] bg-[var(--surface)] p-3 md:p-4" onSubmit={handleSubmit}>
            <div className="mx-auto flex max-w-3xl flex-col gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface-raised)] p-3 shadow-2xl">
              <textarea
                className="min-h-24 resize-none bg-transparent p-2 text-[15px] leading-6 outline-none"
                placeholder="Share what is going on, what feels risky, or what kind of support would help right now..."
                value={input}
                onChange={(event) => setInput(event.target.value)}
              />
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs text-[var(--muted)] md:text-sm">
                  ChatSUD is supportive and safety-first, not clinical care.
                </p>
                <button
                  className="rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-white disabled:opacity-60"
                  type="submit"
                  disabled={isStreaming}
                >
                  Send
                </button>
              </div>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
