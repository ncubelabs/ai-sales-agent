#!/usr/bin/env python3
"""Test MiniMax API with model parameter"""
import os
import sys
import asyncio
import httpx
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_with_models():
    """Test chat completions with different model names"""
    
    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = "https://api.minimax.io"
    
    print(f"🧪 Testing MiniMax chat completions with models...")
    
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0
    ) as client:
        
        # Try different model names found online
        model_names = [
            "abab6.5s-chat",
            "abab6.5-chat", 
            "abab6.5s",
            "abab6.5",
            "abab6",
            "abab5.5-chat",
            "abab5.5s-chat",
            "text-abab6.5s-chat",
            "minimax-abab6.5s-chat",
            "chatglm-6b",
            "claude-3",
            "gpt-3.5-turbo"
        ]
        
        for model_name in model_names:
            try:
                print(f"\n🔍 Testing model: {model_name}")
                
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Hello, respond with just 'Hi there!'"}],
                    "max_tokens": 20
                }
                
                response = await client.post("/v1/chat/completions", json=payload)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ SUCCESS! Model {model_name} works!")
                    print(f"   Response: {data}")
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"   Content: {content}")
                    return model_name
                    
                elif response.status_code == 400:
                    error_text = response.text
                    print(f"   ❌ Error: {error_text}")
                    
                    # Look for specific error messages
                    if "unknown model" in error_text:
                        print(f"   Model '{model_name}' not recognized")
                    elif "insufficient" in error_text.lower() or "quota" in error_text.lower():
                        print(f"   ⚠️ Quota/billing issue with model '{model_name}'")
                    else:
                        print(f"   Other error for model '{model_name}': {error_text}")
                
            except Exception as e:
                print(f"   ❌ Exception with model {model_name}: {e}")
        
        print(f"\n❌ No working model found")
        return None

if __name__ == "__main__":
    working_model = asyncio.run(test_with_models())
    if working_model:
        print(f"\n🎉 Found working model: {working_model}")
    else:
        print(f"\n❌ No working model found")
    sys.exit(0 if working_model else 1)