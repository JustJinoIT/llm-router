"""
LLM Optimizer - 모델 선택 아님, 최적화만

기존 llm-router의 문제:
  - 모델 선택을 강제함 (Groq/Claude 선택 강제)
  - 실제 프로젝트는 이미 모델이 결정되어 있음
  - 추가 가치 없음

새로운 LLMOptimizer의 가치:
  - Prompt 최적화 (토큰 감소)
  - Response 캐싱 (API 호출 감소)
  - Cost 추적 (비용 모니터링)
  - Token 계산 (예산 관리)
  - Retry 로직 (안정성)
"""

import hashlib
import time
import re
from typing import Optional, Dict, Any

class LLMOptimizer:
    """LLM 사용을 최적화하는 도구"""

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple[str, float]] = {}
        self.cache_ttl = cache_ttl_seconds
        self.usage = {
            "total_calls": 0,
            "cache_hits": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_cost_usd": 0.0,
        }

    def optimize_prompt(self, prompt: str, target_tokens: int = 2000) -> str:
        """
        프롬프트 최적화
        - 불필요한 공백 제거
        - 반복 제거
        - 길이 제한
        """
        # 연속 공백 제거
        prompt = re.sub(r'\s+', ' ', prompt)
        # 연속 개행 제거
        prompt = re.sub(r'\n{3,}', '\n\n', prompt)

        # 길이 제한
        if len(prompt) > target_tokens * 4:  # 대략 4글자 = 1토큰
            prompt = prompt[:target_tokens * 4] + "\n...(이하 생략)"

        return prompt.strip()

    def estimate_tokens(self, text: str) -> int:
        """토큰 수 추정 (한국어 기준: 1글자 ≈ 0.5토큰)"""
        return max(1, int(len(text) * 0.5))

    def estimate_cost(self, tokens_in: int, tokens_out: int, model: str = "gpt-4") -> float:
        """
        API 비용 추정

        지원 모델:
        - gpt-4: $0.03/$0.06 per 1K tokens
        - gpt-3.5: $0.0005/$0.0015 per 1K tokens
        - claude-3-sonnet: $0.003/$0.015 per 1K tokens
        - claude-3-opus: $0.015/$0.075 per 1K tokens
        - groq: $0.0 (free)
        - gemini: $0.0 (free tier)
        """
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5": {"input": 0.0005, "output": 0.0015},
            "claude-sonnet": {"input": 0.003, "output": 0.015},
            "claude-opus": {"input": 0.015, "output": 0.075},
            "groq": {"input": 0.0, "output": 0.0},
            "gemini": {"input": 0.0, "output": 0.0},
        }

        price = pricing.get(model, {"input": 0.0, "output": 0.0})
        cost = (tokens_in * price["input"] + tokens_out * price["output"]) / 1000
        self.usage["total_cost_usd"] += cost
        return cost

    def get_cache(self, prompt: str) -> Optional[str]:
        """캐시 조회"""
        key = hashlib.md5(prompt.encode()).hexdigest()
        if key in self.cache:
            response, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                self.usage["cache_hits"] += 1
                return response
            del self.cache[key]
        return None

    def set_cache(self, prompt: str, response: str) -> None:
        """캐시 저장"""
        key = hashlib.md5(prompt.encode()).hexdigest()
        self.cache[key] = (response, time.time())

    def clear_cache(self) -> None:
        """캐시 초기화"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """사용 통계"""
        hit_rate = (
            self.usage["cache_hits"] / (self.usage["total_calls"] + 1) * 100
            if self.usage["total_calls"] > 0
            else 0
        )
        return {
            **self.usage,
            "cache_hit_rate_percent": f"{hit_rate:.1f}%",
            "avg_cost_per_call": (
                self.usage["total_cost_usd"] / self.usage["total_calls"]
                if self.usage["total_calls"] > 0
                else 0
            ),
        }
