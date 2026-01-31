#!/usr/bin/env python3
"""Test official MiniMax model names"""
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

async def test_official_models():
    """Test model names from official MiniMax documentation"""
    
    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = "https://api.minimax.io"
    
    print(f"🧪 Testing official MiniMax model names...")
    
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0
    ) as client:
        
        # Model names from the official site and common conventions
        model_names = [
            # From official site
            "M2.1", "M2-her", "M2", 
            "minimax-m2.1", "minimax-m2-her", "minimax-m2",
            "MiniMax-M2.1", "MiniMax-M2-her", "MiniMax-M2",
            
            # Different naming conventions
            "abab-5.5s-chat", "abab-5.5-chat", "abab-5.5s", "abab-5.5",
            "abab-6.5-s-chat", "abab-6.5-s", 
            "abab5.5s-chat", "abab5.5-chat", "abab5.5s", "abab5.5",
            
            # Alternative patterns
            "text-davinci-003", "text-davinci-002", "davinci",
            "chatglm3-6b", "chatglm2-6b", "chatglm-6b",
            "baichuan2-7b", "baichuan2-13b",
            "qwen-7b-chat", "qwen-14b-chat",
            
            # Just try some numbers
            "abab6-5s-chat", "abab6_5s_chat", "abab6_5s",
            "ABAB6.5s-chat", "ABAB6.5S-CHAT",
        ]
        
        for model_name in model_names:
            try:
                print(f"\n🔍 Testing: {model_name}")
                
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Say hi"}],
                    "max_tokens": 10,
                    "temperature": 0.1
                }
                
                response = await client.post("/v1/chat/completions", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ SUCCESS! Model '{model_name}' works!")
                    print(f"   Full response: {data}")
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0].get("message", {}).get("content", "")
                        print(f"   Content: '{content}'")
                    return model_name
                    
                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "")
                    if "unknown model" in error_msg:
                        print(f"   ❌ Unknown model")
                    else:
                        print(f"   ❌ Other error: {error_msg}")
                
                elif response.status_code == 429:
                    print(f"   ⚠️ Rate limited")
                    
                elif response.status_code == 402:
                    print(f"   💳 Payment required")
                    
                else:
                    print(f"   ❌ Status {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        print(f"\n❌ No working model found from official names")
        return None

if __name__ == "__main__":
    working_model = asyncio.run(test_official_models())
    if working_model:
        print(f"\n🎉 Found working model: {working_model}")
    else:
        print(f"\n💭 No working text models found")
    sys.exit(0 if working_model else 1)