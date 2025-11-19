#!/usr/bin/env python3
"""
Universal Agentic Learning SDK Integration Examples
Demonstrates the 3-line pattern working with multiple LLM providers
"""

import asyncio
import os
from agentic_learning import learning_async

# Provider imports
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class UniversalLLMAgent:
    """Agent that can work with any available LLM provider"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available providers"""
        
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.providers["openai"] = AsyncOpenAI()
            
        if CLAUDE_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.providers["claude"] = AsyncAnthropic()
            
        if GEMINI_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.providers["gemini"] = genai.GenerativeModel('gemini-pro')
    
    async def chat(self, message: str, provider: str = None):
        """Chat with specified or first available provider"""
        
        if not self.providers:
            print("No LLM providers available. Please set API keys.")
            return
        
        if provider is None:
            provider = list(self.providers.keys())[0]
        
        if provider not in self.providers:
            print(f"Provider {provider} not available. Available: {list(self.providers.keys())}")
            return
        
        async with learning_async(agent="universal-agent"):
            if provider == "openai":
                response = await self.providers[provider].chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": message}],
                    max_tokens=500
                )
                return response.choices[0].message.content
                
            elif provider == "claude":
                response = await self.providers[provider].messages.create(
                    model="claude-3-5-sonnet-20241022",
                    messages=[{"role": "user", "content": message}],
                    max_tokens=500
                )
                return response.content[0].text
                
            elif provider == "gemini":
                response = await self.providers[provider].generate_content_async(message)
                return response.text

async def demonstrate_memory_persistence():
    """Demonstrate memory across different providers"""
    
    agent = UniversalLLMAgent()
    
    print("=== Universal Memory Integration Demo ===")
    print(f"Available providers: {list(agent.providers.keys())}")
    
    if not agent.providers:
        return
    
    # First message with first available provider
    provider = list(agent.providers.keys())[0]
    print(f"\n1. First message with {provider}...")
    response1 = await agent.chat(
        "Hi! I'm working on a project about LLM memory integration. Please remember this.",
        provider
    )
    print(f"Response: {response1[:100]}...")
    
    # Second message - can use same or different provider
    print(f"\n2. Follow-up message...")
    response2 = await agent.chat(
        "Can you suggest some best practices for my LLM memory project?",
        provider  # Could use different provider to test cross-provider memory
    )
    print(f"Response: {response2[:100]}...")

async def demonstrate_capture_only_mode():
    """Demonstrate capture-only mode for logging"""
    
    if not OPENAI_AVAILABLE:
        print("OpenAI not available for capture-only demo")
        return
    
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    
    print("\n=== Capture-Only Mode Demo ===")
    
    # Capture-only mode - saves conversation but doesn't inject memory
    async with learning_async(agent="logging-agent", capture_only=True):
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "This will be logged but no memory injected"}],
            max_tokens=200
        )
        print(f"Logged response: {response.choices[0].message.content}")

if __name__ == "__main__":
    asyncio.run(demonstrate_memory_persistence())
    asyncio.run(demonstrate_capture_only_mode())