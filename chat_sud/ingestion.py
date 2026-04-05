from __future__ import annotations

from pathlib import Path

from chat_sud.schemas import DocumentInput, DocumentRecord


def normalize_text(text: str) -> str:
    cleaned = " ".join(text.replace("\x00", " ").split())
    return cleaned.strip()


def parse_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install chat-sud[pdf] to ingest PDF files.") from exc

    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return normalize_text(text)


def load_document(input_doc: DocumentInput) -> DocumentRecord:
    if input_doc.text:
        text = normalize_text(input_doc.text)
        source = input_doc.source or input_doc.title or "inline-document"
    elif input_doc.path:
        path = Path(input_doc.path)
        if not path.exists():
            raise FileNotFoundError(f"Document path does not exist: {path}")
        source = input_doc.source or path.name
        if path.suffix.lower() == ".pdf":
            text = parse_pdf(path)
        else:
            text = normalize_text(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Each document must provide either text or path.")

    title = input_doc.title or source
    substance_category = input_doc.substance_category or "general"
    return DocumentRecord(
        source=source,
        title=title,
        text=text,
        tags=input_doc.tags,
        substance_category=substance_category,
    )


def ingest_documents(documents: list[DocumentInput]) -> list[DocumentRecord]:
    return [load_document(document) for document in documents]

