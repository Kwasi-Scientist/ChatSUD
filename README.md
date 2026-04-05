# 🧠 SUD Therapeutic Counselor (RAG + QLoRA)

A **privacy-first, open-source therapeutic support model** for substance use recovery.  
This project combines **QLoRA fine-tuning**, **Retrieval-Augmented Generation (RAG)** over evidence-based materials (CBT, DBT, Motivational Interviewing), and **explicit safety guardrails** with crisis escalation.

> ⚠️ IMPORTANT: This system is **not a licensed therapist, clinician, or medical device**.  
> It is intended for **research, experimentation, and supportive recovery coaching only**, not diagnosis, treatment, or emergency care.

---

## ✨ Key Features

- 🔒 **Privacy-first by design**
  - Can run locally or in secure environments
  - No requirement to store user conversations
- 📚 **Evidence-grounded**
  - RAG over relapse prevention manuals, CBT/DBT workbooks, MI guides
- 🧩 **End-to-end pipeline**
  - PDF ingestion → chunking → FAISS indexing → QLoRA fine-tuning → inference
- 🛡️ **Safety-aware**
  - Crisis detection with region-aware hotline escalation (US / UK / EU / Global)
  - Explicit refusals for unsafe or disallowed content
- ⚙️ **Hardware-efficient**
  - Designed to run on Google Colab T4 GPUs using 4-bit QLoRA
- 🧪 **Research-friendly**
  - Fully inspectable prompts, datasets, and training artifacts

---

## 🗂️ Repository Structure

├── sud_therapist_pipeline.py # End-to-end pipeline (CLI)
├── TrainingData/ # Open-access PDFs (user-provided)
├── HuggingFace/
│ └── work/
│ ├── corpus_raw.jsonl
│ ├── corpus_chunks.jsonl
│ ├── sft_pairs.jsonl
│ ├── faiss_index/
│ └── haizea-sud-sft/ # Trained LoRA adapter
└── README.md


---

## 🧠 What the Model Does (and Does Not Do)

### ✅ Supported
- Reflective, empathetic dialogue (MI-style)
- Relapse-prevention and coping plans
- Craving and trigger management
- Grounded responses based on vetted materials
- Encouragement to seek professional help

### ❌ Not Supported
- Medical or psychiatric diagnosis
- Medication or detox instructions
- Emergency intervention beyond hotline escalation
- Instructions for illegal or harmful behavior

---

## 🚀 Quick Start (Google Colab or Local)

### 1. Install dependencies
```bash
pip install -U transformers accelerate datasets bitsandbytes \
  peft trl sentencepiece faiss-cpu unstructured[pdf] \
  sentence-transformers


2. Prepare training data

Place open-access PDFs only into:

TrainingData/


3. Parse PDFs into text

python sud_therapist_pipeline.py parse-pdfs \
  --src TrainingData \
  --out HuggingFace/work/corpus_raw.jsonl


4. Build chunks and instruction-tuning pairs


python sud_therapist_pipeline.py build-examples \
  --raw HuggingFace/work/corpus_raw.jsonl \
  --chunks HuggingFace/work/corpus_chunks.jsonl \
  --sft HuggingFace/work/sft_pairs.jsonl


5. Build FAISS index (RAG)

python sud_therapist_pipeline.py build-faiss \
  --chunks HuggingFace/work/corpus_chunks.jsonl \
  --index HuggingFace/work/faiss_index



6. Train QLoRA adapter (T4-friendly)

python sud_therapist_pipeline.py train-sft \
  --base mistralai/Mistral-7B-Instruct-v0.2 \
  --sft HuggingFace/work/sft_pairs.jsonl \
  --out HuggingFace/work/haizea-sud-sft


7. Run inference

python sud_therapist_pipeline.py infer \
  --base mistralai/Mistral-7B-Instruct-v0.2 \
  --adapter HuggingFace/work/haizea-sud-sft \
  --index HuggingFace/work/faiss_index \
  --region US




🛡️ Safety & Crisis Escalation

The system includes a hard-coded safety module that:

Detects self-harm, overdose, and acute crisis language

Immediately interrupts generation

Displays region-aware crisis resources:

United States

988 Suicide & Crisis Lifeline (call or text 988)

United Kingdom

Samaritans: 116 123

Shout: text SHOUT to 85258

European Union

Emergency: 112

Befrienders Worldwide directory

Global fallback

Local emergency number + Befrienders Worldwide

This behavior cannot be overridden by the model.

🔬 Intended Use

AI safety and alignment research

Mental health NLP experimentation

Privacy-preserving support tools

Prototyping recovery coaching workflows

Not intended for clinical or emergency deployment.

📜 Data, Ethics, and Responsibility

You are responsible for:

Ensuring training data is legally usable and properly licensed

Avoiding training on private therapy transcripts without consent

Providing clear user disclosures and limitations

Complying with applicable laws and regulations

🤝 Contributing

Contributions are welcome, especially:

Evaluation benchmarks

Safety improvements

Better RAG routing and filtering

Clinician-reviewed prompt templates

Please open an issue before submitting major changes.

⚠️ Disclaimer

This software provides informational and supportive content only.
It does not replace professional medical, psychological, or emergency services.

If you or someone else is in immediate danger, contact local emergency services.