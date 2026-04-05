from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from chat_sud.schemas import ChunkRecord


GROUNDING_STYLES = {
    "MI": "Use motivational interviewing to reflect ambivalence, affirm strengths, and elicit one small next step.",
    "CBT": "Use CBT framing to connect triggers, thoughts, feelings, and actions with practical coping options.",
    "DBT": "Use DBT distress-tolerance and emotion-regulation skills without sounding clinical or cold.",
}


@dataclass(slots=True)
class QLoRAConfig:
    base_model: str
    output_dir: str
    train_file: str
    validation_file: str
    learning_rate: float = 2e-4
    num_train_epochs: int = 2
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    max_seq_length: int = 2048
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05


def _source_grounding(chunk: ChunkRecord) -> str:
    return (
        f"Source: {chunk.title}. Grounding excerpt: {chunk.snippet}. "
        f"Substance category: {chunk.substance_category}."
    )


def synthesize_grounded_example(chunk: ChunkRecord, style: str) -> dict[str, str | list[str]]:
    instruction = GROUNDING_STYLES[style]
    input_text = (
        "I am having a hard time with cravings and feeling tempted to use tonight. "
        f"{_source_grounding(chunk)} "
        "Please help me make a supportive plan that is realistic for the next few hours."
    )
    output = (
        "It makes sense that the urge feels strong right now, and reaching for support before acting on it is a real strength. "
        f"Based on {chunk.title}, one useful focus is: {chunk.snippet} "
        "For the next few hours, try one grounding action, one connection action, and one environment action. "
        "For example, leave the triggering setting, contact one trusted person or recovery support, and pick a specific coping skill you can do for 10 minutes. "
        "If the urge gets stronger or starts to feel unsafe, shift from self-management to live human support right away."
    )
    return {
        "system": (
            "You are ChatSUD, a non-clinical, safety-first recovery support assistant. "
            "You provide supportive coaching, not diagnosis or medical treatment."
        ),
        "instruction": instruction,
        "input": input_text,
        "output": output,
        "tags": chunk.tags,
        "style": style,
        "source": chunk.source,
        "substance_category": chunk.substance_category,
    }


def build_training_splits(
    chunks: list[ChunkRecord],
    validation_split: float = 0.1,
    seed: int = 42,
) -> dict[str, list[dict[str, str | list[str]]]]:
    examples: list[dict[str, str | list[str]]] = []
    for chunk in chunks:
        for style in GROUNDING_STYLES:
            examples.append(synthesize_grounded_example(chunk, style))
    rng = random.Random(seed)
    rng.shuffle(examples)
    split_at = max(1, int(len(examples) * (1 - validation_split)))
    return {"train": examples[:split_at], "validation": examples[split_at:]}


def write_training_splits(output_dir: Path, dataset: dict[str, list[dict[str, str | list[str]]]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for split_name, rows in dataset.items():
        path = output_dir / f"{split_name}.jsonl"
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )


def evaluate_dataset(dataset: dict[str, list[dict[str, str | list[str]]]]) -> dict[str, int]:
    return {
        "train_examples": len(dataset["train"]),
        "validation_examples": len(dataset["validation"]),
    }


def train_qlora(config: QLoRAConfig) -> dict[str, str | int | float]:
    try:
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
        from trl import SFTTrainer
    except ImportError as exc:
        raise RuntimeError(
            "Install chat-sud[training] to run QLoRA fine-tuning."
        ) from exc

    dataset = load_dataset(
        "json",
        data_files={"train": config.train_file, "validation": config.validation_file},
    )
    tokenizer = AutoTokenizer.from_pretrained(config.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype="bfloat16",
    )
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        quantization_config=quantization,
        device_map="auto",
        trust_remote_code=True,
    )
    lora = LoraConfig(
        r=config.lora_rank,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    args = TrainingArguments(
        output_dir=config.output_dir,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_steps=20,
        report_to="none",
    )
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        args=args,
        max_seq_length=config.max_seq_length,
    )
    trainer.train()
    trainer.model.save_pretrained(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)
    return asdict(config)

