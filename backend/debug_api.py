#!/usr/bin/env python3
"""Debug MiniMax API to find working endpoints"""
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

async def debug_api():
    """Test different endpoints to understand API structure"""
    
    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = "https://api.minimax.io"
    
    print(f"🔍 Debugging MiniMax API at {base_url}")
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0
    ) as client:
        
        # Try different endpoint patterns
        endpoints = [
            "/v1/chat/completions",
            "/v1/completions", 
            "/v1/text/generation",
            "/v1/generate",
            "/chat/completions",
            "/completions",
            "/text/generation",
            "/generate",
            "/v1/models",
            "/models",
            "/",
            "/v1/",
            "/api/v1/chat/completions",
            "/api/chat/completions",
        ]
        
        for endpoint in endpoints:
            try:
                print(f"\n🔍 Testing endpoint: {endpoint}")
                
                # First try GET (for models endpoint)
                try:
                    response = await client.get(endpoint)
                    if response.status_code in [200, 405]:  # 405 means method not allowed but endpoint exists
                        print(f"   ✅ GET {endpoint} -> {response.status_code}")
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                print(f"   📄 Response: {data}")
                            except:
                                print(f"   📄 Response: {response.text[:200]}...")
                    else:
                        print(f"   ❌ GET {endpoint} -> {response.status_code}")
                except Exception as e:
                    print(f"   ❌ GET {endpoint} -> {e}")
                
                # Then try POST with a simple payload
                if "chat" in endpoint.lower() or "completion" in endpoint.lower() or "generate" in endpoint.lower():
                    try:
                        payload = {
                            "prompt": "Hello",
                            "max_tokens": 10
                        }
                        response = await client.post(endpoint, json=payload)
                        print(f"   📤 POST {endpoint} (simple) -> {response.status_code}")
                        if response.status_code not in [404, 405]:
                            print(f"   📄 Response: {response.text[:200]}...")
                        
                        # Try chat format
                        payload = {
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 10
                        }
                        response = await client.post(endpoint, json=payload)
                        print(f"   📤 POST {endpoint} (chat) -> {response.status_code}")
                        if response.status_code not in [404, 405]:
                            print(f"   📄 Response: {response.text[:200]}...")
                            
                    except Exception as e:
                        print(f"   ❌ POST {endpoint} -> {e}")
                        
            except Exception as e:
                print(f"   ❌ Error testing {endpoint}: {e}")

if __name__ == "__main__":
    asyncio.run(debug_api())