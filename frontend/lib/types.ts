export type RetrievedSource = {
  source: string;
  title: string;
  snippet: string;
  score: number;
  tags: string[];
  substance_category: string;
};

export type ChatResponse = {
  assistant_message: string;
  safety_escalation_triggered: boolean;
  safety_mode: "supportive" | "crisis" | "medical_refusal";
  retrieved_sources: RetrievedSource[];
  session_id: string;
};

