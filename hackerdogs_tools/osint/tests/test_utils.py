"""
Test utilities for OSINT tools
"""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from crewai import Agent, Task, Crew
from crewai.llm import LLM

# Load environment variables
load_dotenv(override=True)


def get_llm_from_env() -> BaseChatModel:
    """
    Get LLM from environment variables.
    
    Environment variables:
    - MODEL: Model identifier (e.g., "ollama/gemma2:2b", "openai/gpt-4", "anthropic/claude-3-5-sonnet")
    - LLM_API_KEY: API key for the provider
    - PROVIDER_BASE_URL: Base URL for the provider (important for Ollama)
    
    Returns:
        BaseChatModel instance
    """
    model = os.getenv("MODEL", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("PROVIDER_BASE_URL", "").strip()
    
    if not model:
        raise ValueError("MODEL environment variable not set")
    
    # Parse model format: provider/model_name
    if "/" in model:
        provider, model_name = model.split("/", 1)
    else:
        provider = "openai"
        model_name = model
    
    provider = provider.lower()
    
    if provider == "ollama":
        if not base_url:
            base_url = "http://localhost:11434"
        return ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.1
        )
    elif provider == "openai":
        if not api_key:
            raise ValueError("LLM_API_KEY required for OpenAI")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0.1
        )
    elif provider == "anthropic":
        if not api_key:
            raise ValueError("LLM_API_KEY required for Anthropic")
        return ChatAnthropic(
            model=model_name,
            api_key=api_key,
            temperature=0.1
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}. Supported: ollama, openai, anthropic")


def get_crewai_llm_from_env() -> LLM:
    """
    Get CrewAI LLM from environment variables.
    
    Returns:
        LLM instance for CrewAI
    """
    model = os.getenv("MODEL", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("PROVIDER_BASE_URL", "").strip()
    
    if not model:
        raise ValueError("MODEL environment variable not set")
    
    # Parse model format: provider/model_name
    if "/" in model:
        provider, model_name = model.split("/", 1)
    else:
        provider = "openai"
        model_name = model
    
    provider = provider.lower()
    
    if provider == "ollama":
        if not base_url:
            base_url = "http://localhost:11434"
        return LLM(
            model=f"ollama/{model_name}",
            base_url=base_url
        )
    elif provider == "openai":
        if not api_key:
            raise ValueError("LLM_API_KEY required for OpenAI")
        return LLM(
            model=model_name,
            api_key=api_key
        )
    elif provider == "anthropic":
        if not api_key:
            raise ValueError("LLM_API_KEY required for Anthropic")
        return LLM(
            model=model_name,
            api_key=api_key
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}. Supported: ollama, openai, anthropic")

