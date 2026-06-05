"""
LLM Router — 무료 우선 + 토큰 효율 자동 선택

[모델 우선순위]
  1. Groq llama-3.3-70b — 무료, 초고속
  2. Groq gemma2-9b     — 폴백
  3. Anthropic Claude   — 유료 (필요시)

[기능]
  - 프롬프트 길이로 모델 자동 선택
  - 응답 캐싱 (해시 기반)
  - 토큰 사용량 추적
  - 프롬프트 압축
"""

import asyncio
import hashlib
import re
import time
from typing import Optional
import os


_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 3600
_usage = {"calls": 0, "est_tokens_in": 0, "est_tokens_out": 0, "cache_hits": 0}


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _cache_get(key: str) -> Optional[str]:
    if key in _cache:
        val, ts = _cache[key]
        if time.time() - ts < _CACHE_TTL:
            _usage["cache_hits"] += 1
            return val
        del _cache[key]
    return None


def _cache_set(key: str, val: str) -> None:
    _cache[key] = (val, time.time())


def compress_prompt(prompt: str) -> str:
    """토큰 절약: 불필요한 공백/반복 제거."""
    prompt = re.sub(r'\n{3,}', '\n\n', prompt)
    prompt = re.sub(r'[ \t]{2,}', ' ', prompt)
    return prompt.strip()


def trim_context(context: str, budget_chars: int = 2000) -> str:
    """RAG 컨텍스트 길이 제한."""
    if len(context) <= budget_chars:
        return context
    return context[:budget_chars] + "\n...(이하 생략)"


def _estimate_tokens(text: str) -> int:
    """토큰 추정 (글자 수 / 2)."""
    return max(1, len(text) // 2)


def _pick_model(prompt: str, prefer_cheap: bool = True) -> str:
    """
    프롬프트 길이로 모델 자동 선택.

    Args:
        prompt: 입력 프롬프트
        prefer_cheap: True면 무료 모델 우선

    Returns:
        모델명 ('groq-70b', 'groq-9b', 'claude-3-5-sonnet', 등)
    """
    n = len(prompt)

    if prefer_cheap:
        if n < 2000:
            return "groq-9b"
        elif n < 10000:
            return "groq-70b"
        else:
            return "claude-3-5-sonnet"
    else:
        return "claude-3-5-sonnet"


class LLMRouter:
    def __init__(self, groq_api_key: str = None, claude_api_key: str = None):
        """
        Args:
            groq_api_key: Groq API 키 (env: GROQ_API_KEY)
            claude_api_key: Anthropic API 키 (env: ANTHROPIC_API_KEY)
        """
        self.groq_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.claude_key = claude_api_key or os.getenv("ANTHROPIC_API_KEY")
        self._usage = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cache_hits": 0}

    async def generate(
        self,
        prompt: str,
        system: str = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_cache: bool = True,
    ) -> str:
        """
        LLM에 프롬프트 요청.

        Args:
            prompt: 사용자 입력
            system: 시스템 프롬프트
            model: 모델명 (None이면 자동 선택)
            temperature: 창의성 (0~2)
            max_tokens: 응답 길이
            use_cache: 응답 캐싱 사용 여부

        Returns:
            LLM 응답 텍스트
        """
        # 캐시 확인
        cache_key = _hash(prompt + (system or ""))
        if use_cache:
            cached = _cache_get(cache_key)
            if cached:
                return cached

        # 모델 선택
        if model is None:
            model = _pick_model(prompt)

        # 프롬프트 압축
        prompt = compress_prompt(prompt)

        # API 호출
        if model.startswith("groq"):
            response = await self._groq_call(prompt, system, model, temperature, max_tokens)
        else:
            response = await self._claude_call(prompt, system, temperature, max_tokens)

        # 캐시 저장
        if use_cache:
            _cache_set(cache_key, response)

        # 통계 기록
        self._usage["calls"] += 1
        self._usage["tokens_in"] += _estimate_tokens(prompt)
        self._usage["tokens_out"] += _estimate_tokens(response)

        return response

    async def _groq_call(self, prompt: str, system: str, model: str, temp: float, max_tk: int) -> str:
        """Groq API 호출."""
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY not set")

        try:
            from groq import Groq
        except ImportError:
            raise ImportError("groq library required: pip install groq")

        client = Groq(api_key=self.groq_key)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tk,
        )

        return response.choices[0].message.content

    async def _claude_call(self, prompt: str, system: str, temp: float, max_tk: int) -> str:
        """Claude API 호출."""
        if not self.claude_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic library required: pip install anthropic")

        client = Anthropic(api_key=self.claude_key)

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tk,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
        )

        return response.content[0].text

    def get_usage(self) -> dict:
        """토큰 사용량 조회."""
        return self._usage.copy()

    def clear_cache(self) -> None:
        """응답 캐시 초기화."""
        global _cache
        _cache.clear()
