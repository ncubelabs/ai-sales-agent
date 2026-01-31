#!/usr/bin/env python3
"""Check API key permissions and try alternative approaches"""
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

async def check_api_permissions():
    """Check what we can access with this API key"""
    
    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = "https://api.minimax.io"
    
    print(f"🔍 Checking API key permissions...")
    print(f"🔑 API Key: {api_key[:20]}...{api_key[-4:]}")
    print(f"🌐 Base URL: {base_url}")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
        
        # Try different authentication formats
        auth_formats = [
            {"Authorization": f"Bearer {api_key}"},
            {"Authorization": f"Api-Key {api_key}"},
            {"X-API-Key": api_key},
            {"api-key": api_key},
            {"apikey": api_key},
        ]
        
        for i, auth_header in enumerate(auth_formats):
            print(f"\n🔐 Testing auth format {i+1}: {list(auth_header.keys())[0]}")
            
            try:
                client.headers = auth_header
                
                # Try to get models with this auth format
                response = await client.get("/v1/models")
                print(f"   GET /v1/models -> {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ Models endpoint works! {response.json()}")
                elif response.status_code == 401:
                    print(f"   ❌ Authentication failed")
                elif response.status_code == 403:
                    print(f"   ❌ Forbidden - key might not have model access")
                elif response.status_code == 404:
                    print(f"   ❌ Endpoint not found")
                else:
                    print(f"   ❓ Other status: {response.text}")
                
                # Try chat completions without model (to see if auth works)
                payload = {
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                }
                
                response = await client.post("/v1/chat/completions", json=payload)
                print(f"   POST /v1/chat/completions (no model) -> {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ Chat endpoint works! {response.json()}")
                elif response.status_code == 400:
                    error_text = response.text
                    if "model" in error_text.lower():
                        print(f"   ✅ Auth works, just missing model parameter")
                        print(f"   Error details: {error_text}")
                    else:
                        print(f"   ❌ Different error: {error_text}")
                elif response.status_code == 401:
                    print(f"   ❌ Authentication failed")
                elif response.status_code == 403:
                    print(f"   ❌ Forbidden")
                else:
                    print(f"   ❓ Other error: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Try other endpoints that might exist
        print(f"\n🔍 Testing other potential endpoints...")
        other_endpoints = [
            "/user/info", "/account", "/usage", "/quota", "/billing",
            "/v1/user", "/v1/account", "/v1/usage", 
            "/api/models", "/api/user", "/api/account"
        ]
        
        for endpoint in other_endpoints:
            try:
                response = await client.get(endpoint)
                if response.status_code not in [404, 405]:
                    print(f"   GET {endpoint} -> {response.status_code}: {response.text[:100]}...")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(check_api_permissions())