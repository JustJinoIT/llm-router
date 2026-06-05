# LLM Router 🤖

무료 우선, 토큰 효율적인 LLM 자동 선택 라이브러리.

## 특징

- 🚀 **무료 우선**: Groq (무료) → Claude (유료)
- ⚡ **자동 선택**: 프롬프트 길이로 모델 자동 선택
- 💾 **응답 캐싱**: 동일 입력 → 즉시 응답
- 📊 **토큰 추적**: 사용량 자동 기록
- 🎯 **프롬프트 압축**: 불필요한 공백 자동 제거

## 설치

```bash
pip install llm-router
```

## 사용법

```python
import asyncio
from llm_router import LLMRouter

router = LLMRouter(
    groq_api_key="gsk_...",
    claude_api_key="sk-..."
)

async def main():
    response = await router.generate(
        prompt="한국의 수도는?",
        system="간단하고 정확하게 답변해."
    )
    print(response)
    print(router.get_usage())

asyncio.run(main())
```

## API

### `LLMRouter(groq_api_key, claude_api_key)`

초기화.

### `await router.generate(prompt, system=None, model=None, temperature=0.7, max_tokens=1000, use_cache=True)`

LLM에 요청.

- `model`: `None`이면 프롬프트 길이로 자동 선택
  - < 2000자: `groq-9b` (빠르고 가벼움)
  - 2000~10000자: `groq-70b` (균형)
  - \> 10000자: `claude-3-5-sonnet` (정확함)

### `router.get_usage()`

토큰 사용량 조회.

```python
{
    "calls": 5,
    "tokens_in": 1200,
    "tokens_out": 450,
    "cache_hits": 2
}
```

### `router.clear_cache()`

응답 캐시 초기화.

## 환경 변수

```bash
export GROQ_API_KEY=gsk_...
export ANTHROPIC_API_KEY=sk-...
```

또는 초기화 시 직접 지정:

```python
router = LLMRouter(
    groq_api_key="gsk_...",
    claude_api_key="sk-..."
)
```

## 라이선스

MIT
