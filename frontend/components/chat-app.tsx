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
    if (!trimmed) return;

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
    <main className="min-h-screen p-4 text-[var(--text)] md:p-6">
      <SettingsPanel
        open={settingsOpen}
        region={region}
        privacyMode={privacyMode}
        onClose={() => setSettingsOpen(false)}
        onRegionChange={setRegion}
        onPrivacyChange={setPrivacyMode}
      />
      <SourceDrawer open={drawerOpen} sources={drawerSources} onClose={() => setDrawerOpen(false)} />

      <div className="mx-auto flex min-h-[calc(100vh-2rem)] max-w-7xl gap-4">
        <aside className="glass hidden w-72 shrink-0 rounded-[28px] p-4 md:flex md:flex-col">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">ChatSUD</p>
              <h1 className="text-2xl font-semibold">Recovery workspace</h1>
            </div>
            <button className="rounded-full border px-3 py-2 text-sm" onClick={createSession}>
              New
            </button>
          </div>
          <button
            className="mb-4 rounded-2xl border border-[var(--border)] bg-white/70 px-4 py-3 text-left text-sm"
            onClick={() => setSettingsOpen(true)}
          >
            Region: {region}
            <br />
            Privacy mode: {privacyMode ? "On" : "Off"}
          </button>
          <div className="space-y-2 overflow-y-auto">
            {sessions.map((session) => (
              <button
                key={session.id}
                className={`w-full rounded-2xl px-4 py-3 text-left ${session.id === activeSessionId ? "bg-[var(--accent)] text-white" : "bg-white/70"}`}
                onClick={() => setActiveSessionId(session.id)}
              >
                <p className="truncate font-semibold">{session.title}</p>
                <p className="truncate text-xs opacity-80">
                  {session.messages.at(-1)?.content ?? "Start a new supportive conversation"}
                </p>
              </button>
            ))}
          </div>
        </aside>

        <section className="glass flex flex-1 flex-col rounded-[32px]">
          <header className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">Non-clinical support</p>
              <h2 className="text-xl font-semibold">Safety-first recovery chat</h2>
            </div>
            <div className="flex items-center gap-2">
              <input
                className="rounded-full border border-[var(--border)] bg-white px-4 py-2 text-sm"
                value={substanceHint}
                onChange={(event) => setSubstanceHint(event.target.value)}
                placeholder="Substance hint"
              />
              <button className="rounded-full border px-3 py-2 text-sm md:hidden" onClick={() => setSettingsOpen(true)}>
                Settings
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
            {activeSession.messages.length === 0 ? (
              <div className="mx-auto flex max-w-3xl flex-col items-start gap-6 rounded-[28px] border border-[var(--border)] bg-white/70 p-8">
                <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs uppercase tracking-[0.25em]">
                  Welcome
                </span>
                <h3 className="text-4xl font-semibold leading-tight">
                  A calmer, privacy-first space for recovery support.
                </h3>
                <p className="max-w-2xl text-lg text-[var(--muted)]">
                  ChatSUD offers supportive, non-clinical guidance grounded in indexed recovery materials.
                  It is not emergency care, diagnosis, or medical treatment.
                </p>
              </div>
            ) : (
              <div className="mx-auto flex max-w-3xl flex-col gap-5">
                {activeSession.messages.map((message, index) => (
                  <article
                    key={`${message.role}-${index}`}
                    className={`rounded-[28px] px-5 py-4 shadow-sm ${message.role === "user" ? "ml-auto max-w-[80%] bg-[var(--text)] text-white" : "mr-auto max-w-[88%] bg-white/80"}`}
                  >
                    <p className="whitespace-pre-wrap text-[15px] leading-7">{message.content}</p>
                    {message.safetyMode && message.safetyMode !== "supportive" ? (
                      <div className="mt-4 rounded-2xl border border-[var(--accent)] bg-[var(--accent-soft)] p-3 text-sm">
                        Safety escalation engaged: {message.safetyMode.replace("_", " ")}
                      </div>
                    ) : null}
                    {message.sources?.length ? (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {message.sources.map((source) => (
                          <button
                            key={`${source.source}-${source.title}`}
                            className="rounded-full border border-[var(--border)] px-3 py-1 text-xs text-[var(--muted)]"
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
                  </article>
                ))}
                {isStreaming || isPending ? (
                  <div className="dot-wave rounded-full bg-white/80 px-4 py-3 text-sm text-[var(--muted)]">
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <form className="border-t border-[var(--border)] p-4 md:p-5" onSubmit={handleSubmit}>
            <div className="mx-auto flex max-w-3xl flex-col gap-3 rounded-[28px] border border-[var(--border)] bg-white/80 p-3">
              <textarea
                className="min-h-28 resize-none rounded-[22px] bg-transparent p-3 outline-none"
                placeholder="Share what is going on, what feels risky, or what kind of support would help right now..."
                value={input}
                onChange={(event) => setInput(event.target.value)}
              />
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm text-[var(--muted)]">
                  ChatSUD is supportive and safety-first, not clinical care.
                </p>
                <button
                  className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white"
                  type="submit"
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
