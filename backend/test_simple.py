#!/usr/bin/env python3
"""Simple test of MiniMax text generation"""
import os
import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from services.minimax import MiniMaxClient

# Load environment variables
load_dotenv()

async def test_simple():
    """Simple test of text generation"""
    
    print("🧪 Testing MiniMax text generation...")
    
    try:
        client = MiniMaxClient()
        print("✅ Client initialized")
        
        response = await client.generate_text("Hello, please respond with a short greeting.")
        print(f"✅ Text generation successful!")
        print(f"Response: {response}")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple())
    sys.exit(0 if success else 1)