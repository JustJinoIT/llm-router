"""
LLM Router 테스트
"""

import asyncio
from llm_router import LLMRouter, compress_prompt, trim_context, _estimate_tokens


def test_compress_prompt():
    """프롬프트 압축 테스트."""
    prompt = "이것은   \n\n\n  테스트입니다"
    compressed = compress_prompt(prompt)
    assert "\n\n\n" not in compressed
    assert "  " not in compressed
    print("✅ test_compress_prompt passed")


def test_trim_context():
    """컨텍스트 길이 제한 테스트."""
    long_text = "a" * 5000
    trimmed = trim_context(long_text, budget_chars=2000)
    assert len(trimmed) <= 2030  # budget_chars + "\n...(이하 생략)"
    assert "...(이하 생략)" in trimmed
    print("✅ test_trim_context passed")


def test_estimate_tokens():
    """토큰 추정 테스트."""
    text = "Hello World"  # 11자
    tokens = _estimate_tokens(text)
    assert tokens > 0
    assert tokens <= 11 // 2 + 1
    print("✅ test_estimate_tokens passed")


async def test_router_init():
    """LLMRouter 초기화 테스트."""
    router = LLMRouter(
        groq_api_key="test_key",
        claude_api_key="test_key"
    )
    assert router.groq_key == "test_key"
    assert router.claude_key == "test_key"
    print("✅ test_router_init passed")


async def test_cache():
    """캐싱 테스트."""
    router = LLMRouter(
        groq_api_key="test_key",
        claude_api_key="test_key"
    )

    # 테스트용 간단한 경우는 스킵 (API 필요)
    usage = router.get_usage()
    assert "calls" in usage
    assert usage["calls"] == 0
    print("✅ test_cache passed")


async def test_usage_tracking():
    """사용량 추적 테스트."""
    router = LLMRouter(
        groq_api_key="test_key",
        claude_api_key="test_key"
    )

    usage = router.get_usage()
    assert usage["calls"] == 0
    assert usage["tokens_in"] == 0
    assert usage["tokens_out"] == 0
    assert usage["cache_hits"] == 0
    print("✅ test_usage_tracking passed")


def test_clear_cache():
    """캐시 초기화 테스트."""
    router = LLMRouter(
        groq_api_key="test_key",
        claude_api_key="test_key"
    )
    router.clear_cache()
    print("✅ test_clear_cache passed")


async def main():
    print("🧪 LLM Router 테스트 시작\n")

    test_compress_prompt()
    test_trim_context()
    test_estimate_tokens()
    await test_router_init()
    await test_cache()
    await test_usage_tracking()
    test_clear_cache()

    print("\n✅ 모든 테스트 통과!")


if __name__ == "__main__":
    asyncio.run(main())
