#!/usr/bin/env python3
"""
Research Agent with Memory Integration
Demonstrates how to build a research agent that maintains context across sessions
"""

import asyncio
import os
from anthropic import Anthropic
from agentic_learning import learning_async, AsyncAgenticLearning

class ResearchAgent:
    """A research agent that maintains memory of research topics and findings"""
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.agent_name = "research-assistant"
    
    async def research(self, topic: str, depth: str = "comprehensive"):
        """Research a topic with memory of previous research"""
        
        async with learning_async(
            agent=self.agent_name,
            memory=[
                {"label": "research_history", "description": "Previous research topics and findings"},
                {"label": "current_session", "description": "Current research session context"},
                {"label": "research_methods", "description": "Research approaches and methodologies"}
            ]
        ):
            prompt = f"""
            Research the following topic: {topic}
            
            Depth: {depth}
            
            Please provide:
            1. Key findings and insights
            2. Important sources or references
            3. Connections to previous research if any
            4. Follow-up research suggestions
            
            Consider any previous research context and build upon it.
            """
            
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
    
    async def summarize_session(self):
        """Get a summary of the current research session"""
        
        async with learning_async(agent=self.agent_name):
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user", 
                    "content": "Please provide a brief summary of our research session so far."
                }]
            )
            return response.content[0].text
    
    async def clear_research_memory(self):
        """Clear research memory for a fresh start"""
        client = AsyncAgenticLearning()
        await client.clear_memory(self.agent_name)
        print("Research memory cleared")

async def research_demo():
    """Demonstration of research agent with memory"""
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return
    
    agent = ResearchAgent(api_key)
    
    print("=== Research Agent Demo ===")
    
    # Research topic 1
    print("\n1. Researching 'Memory Integration in AI Systems'...")
    result1 = await agent.research("Memory Integration in AI Systems", "overview")
    print(result1[:500] + "..." if len(result1) > 500 else result1)
    
    # Research topic 2 (will build on previous context)
    print("\n2. Researching 'Vector Databases for AI Memory'...")
    result2 = await agent.research("Vector Databases for AI Memory", "technical")
    print(result2[:500] + "..." if len(result2) > 500 else result2)
    
    # Get session summary
    print("\n3. Session Summary:")
    summary = await agent.summarize_session()
    print(summary)

if __name__ == "__main__":
    asyncio.run(research_demo())