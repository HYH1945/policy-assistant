# Policy Assistant

외부 API 키나 추가 패키지 없이 RAG의 **수집 → 청킹 → 임베딩 → 벡터 저장 → 하이브리드 검색 → 근거 제시** 흐름을 경험하는 작은 프로젝트입니다.

> 이 버전은 생성형 AI가 답을 새로 작성하지 않고, 검색된 근거 문장을 그대로 보여주는 retrieval-first MVP입니다. 데이터는 모두 가상 회사용 합성 문서입니다.

## 실행

```powershell
python app.py index
python app.py ask "수습 직원도 재택근무할 수 있나요?"
```

`index` 명령은 `data/company_docs.json`을 문단 단위로 나누고 각 청크를 벡터로 변환해 `data/index.json`에 저장합니다.

다른 예시 질문:

```powershell
python app.py ask "부산 출장 숙박비 한도는 얼마인가요?"
python app.py ask "노트북을 잃어버렸을 때 어떻게 해야 하나요?"
python app.py ask "연차는 며칠 전에 신청해야 하나요?"
python app.py ask "재택근무 중 카페 와이파이를 써도 되나요?"
```

검색 결과 개수와 카테고리를 지정할 수도 있습니다.

```powershell
python app.py ask "숙박비 기준" --top-k 2 --category 출장
```

## 관찰할 부분

- `chunk_text()`: 문서가 검색 단위로 나뉘는 과정
- `embed()`: 텍스트가 고정 길이 벡터로 변환되는 과정
- `cosine_similarity()`: 질문과 문서 청크의 유사도 계산
- `search()`: 벡터 점수 70%와 정확한 단어 일치 점수 30%를 결합하고 메타데이터·최신 문서를 필터링하는 과정
- `extract_evidence()`: 검색 결과에서 근거 문장을 고르는 과정

## 다음 단계

1. 직접 질문 20개와 정답 청크를 만들어 `Recall@3`를 계산합니다.
2. 문단 청킹과 고정 글자 수 청킹을 비교합니다.
3. `embed()`를 실제 임베딩 API 또는 sentence-transformers로 교체합니다.
4. `data/index.json`을 PostgreSQL + pgvector나 Qdrant로 교체합니다.
5. 검색된 근거만 사용하도록 프롬프트를 구성해 LLM 생성 단계를 추가합니다.

현재 임베딩은 학습 목적의 해시 기반 벡터이므로 의미가 완전히 다른 동의어를 잘 찾지 못합니다. 대신 구현이 짧아 벡터화와 유사도 검색 원리를 직접 따라가기 좋습니다.
