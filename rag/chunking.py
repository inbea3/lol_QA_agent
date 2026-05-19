from __future__ import annotations


def split_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str] | None = None,
) -> list[str]:
    """按分隔符递归分块，语义与 RecursiveCharacterTextSplitter 类似。"""
    seps = separators or ["\n## ", "\n### ", "\n", "。", " ", ""]
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    for i, sep in enumerate(seps):
        if sep == "":
            for start in range(0, len(text), chunk_size - chunk_overlap):
                piece = text[start : start + chunk_size].strip()
                if piece:
                    chunks.append(piece)
            return chunks

        if sep not in text:
            continue

        parts = text.split(sep)
        buffer = ""
        rest_seps = seps[i + 1 :]
        for j, part in enumerate(parts):
            segment = part + (sep if j < len(parts) - 1 else "")
            candidate = buffer + segment
            if len(candidate) <= chunk_size:
                buffer = candidate
            else:
                if buffer.strip():
                    if len(buffer) > chunk_size and rest_seps:
                        chunks.extend(
                            split_text(buffer, chunk_size, chunk_overlap, rest_seps)
                        )
                    else:
                        chunks.append(buffer.strip())
                buffer = segment
        if buffer.strip():
            if len(buffer) > chunk_size and rest_seps:
                chunks.extend(split_text(buffer, chunk_size, chunk_overlap, rest_seps))
            else:
                chunks.append(buffer.strip())
        return [c for c in chunks if c]

    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]
