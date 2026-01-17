#!/usr/bin/env python3
"""
Jarvis AI Assistant - Main Entry Point

A voice-activated AI assistant with calendar management, live translation,
and weather queries using a multiagent architecture.
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/jarvis.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""
    logger.info("🚀 Starting Jarvis AI Assistant...")
    
    # Initialize Orchestrator Agent
    from agents.orchestrator import OrchestratorAgent
    orchestrator = OrchestratorAgent()
    
    logger.info("✅ Jarvis is ready! Say 'Hey Jarvis' to activate.")
    print("\n" + "="*50)
    print("🎤 JARVIS AI ASSISTANT - PHASE 1")
    print("="*50)
    print("Using OpenWakeWord (open source, no API key needed!)")
    print("Say 'Hey Jarvis' to activate the wake word detection!")
    print("Press Ctrl+C to exit")
    print("="*50 + "\n")
    
    # Start the orchestrator (which starts wake word detection)
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down Jarvis...")
        await orchestrator.stop()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await orchestrator.stop()


if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)

