from setuptools import setup

setup(
    name="llm-router",
    version="0.1.0",
    description="LLM Router — Groq/Claude 자동 선택 + 토큰 최적화",
    author="JustJino",
    author_email="215104400+JustJinoIT@users.noreply.github.com",
    url="https://github.com/justjiinoit/llm-router",
    py_modules=["llm_router"],
    python_requires=">=3.9",
    install_requires=[
        "groq>=0.7.0",
        "anthropic>=0.25.0",
        "tenacity>=8.2.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
