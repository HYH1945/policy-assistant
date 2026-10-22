from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DOCS_PATH = BASE_DIR / "data" / "company_docs.json"
INDEX_PATH = BASE_DIR / "data" / "index.json"
VECTOR_SIZE = 512


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def features(text: str) -> list[str]:
    """한국어 단어와 공백을 제거한 문자열의 2/3-gram을 함께 사용한다."""
    normalized = normalize(text)
    words = re.findall(r"[가-힣a-z0-9]+", normalized)
    compact = re.sub(r"[^가-힣a-z0-9]", "", normalized)
    ngrams = [compact[i : i + n] for n in (2, 3) for i in range(len(compact) - n + 1)]
    return words + ngrams


def embed(text: str) -> list[float]:
    """Feature hashing으로 고정 길이 벡터를 만든 뒤 L2 정규화한다."""
    vector = [0.0] * VECTOR_SIZE
    for token, count in Counter(features(text)).items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest, "big") % VECTOR_SIZE
        vector[index] += 1.0 + math.log(count)

    length = math.sqrt(sum(value * value for value in vector))
    return [value / length for value in vector] if length else vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def keyword_coverage(query: str, content: str) -> float:
    """질문의 정확한 단어가 청크에 얼마나 포함되는지 계산한다."""
    query_words = set(re.findall(r"[가-힣a-z0-9]+", normalize(query)))
    content_words = set(re.findall(r"[가-힣a-z0-9]+", normalize(content)))
    return len(query_words & content_words) / len(query_words) if query_words else 0.0


def chunk_text(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]


def build_index() -> list[dict]:
    documents = json.loads(DOCS_PATH.read_text(encoding="utf-8"))
    chunks: list[dict] = []

    for document in documents:
        for position, content in enumerate(chunk_text(document["content"]), start=1):
            chunk = {
                "chunk_id": f'{document["doc_id"]}#{position}',
                "doc_id": document["doc_id"],
                "title": document["title"],
                "category": document["category"],
                "version": document["version"],
                "effective_date": document["effective_date"],
                "status": document["status"],
                "content": content,
                "vector": embed(content),
            }
            chunks.append(chunk)

    INDEX_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    return chunks


def load_index() -> list[dict]:
    if not INDEX_PATH.exists():
        return build_index()
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def search(query: str, top_k: int = 3, category: str | None = None) -> list[dict]:
    query_vector = embed(query)
    candidates = []

    for chunk in load_index():
        if chunk["status"] != "active":
            continue
        if category and chunk["category"] != category:
            continue
        result = {key: value for key, value in chunk.items() if key != "vector"}
        vector_score = cosine_similarity(query_vector, chunk["vector"])
        lexical_score = keyword_coverage(query, chunk["content"])
        result["vector_score"] = vector_score
        result["lexical_score"] = lexical_score
        result["score"] = 0.7 * vector_score + 0.3 * lexical_score
        candidates.append(result)

    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:top_k]


def extract_evidence(query: str, results: list[dict]) -> str:
    """최상위 청크 전체를 근거로 반환해 예외 조건을 잘라내지 않는다."""
    if not results or results[0]["score"] <= 0:
        return "관련 근거를 찾지 못했습니다."
    return results[0]["content"]


def ask(query: str, top_k: int, category: str | None) -> None:
    results = search(query, top_k=top_k, category=category)
    print(f"\n질문: {query}")
    print(f"근거 기반 응답: {extract_evidence(query, results)}")
    print("\n검색 결과")
    for rank, result in enumerate(results, start=1):
        print(
            f'{rank}. [{result["title"]} v{result["version"]} / '
            f'{result["chunk_id"]}] score={result["score"]:.3f} '
            f'(vector={result["vector_score"]:.3f}, keyword={result["lexical_score"]:.3f})'
        )
        print(f'   {result["content"]}')


def main() -> None:
    parser = argparse.ArgumentParser(description="가상 사내 규정 벡터 검색기")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("index", help="문서를 청킹하고 벡터 인덱스를 생성합니다.")

    ask_parser = subparsers.add_parser("ask", help="규정에 질문합니다.")
    ask_parser.add_argument("query")
    ask_parser.add_argument("--top-k", type=int, default=3)
    ask_parser.add_argument("--category", choices=["인사", "출장", "IT"])

    args = parser.parse_args()
    if args.command == "index":
        chunks = build_index()
        print(f"{len(chunks)}개 청크를 {INDEX_PATH}에 저장했습니다.")
    else:
        ask(args.query, args.top_k, args.category)


if __name__ == "__main__":
    main()
