#!/usr/bin/env python3
"""Test different video generation endpoints"""
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

async def test_video_endpoints():
    """Test different video generation endpoints"""
    
    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = "https://api.minimax.io"
    
    print(f"🎥 Testing video generation endpoints...")
    
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0
    ) as client:
        
        video_endpoints = [
            "/v1/video/generation",
            "/v1/video/generate", 
            "/video/generation",
            "/video/generate",
            "/v1/video",
            "/video",
            "/v1/t2v",
            "/t2v",
            "/v1/hailuo",
            "/hailuo",
            "/v1/text-to-video",
            "/text-to-video",
            "/api/video/generation",
            "/api/v1/video/generation",
        ]
        
        test_payload = {
            "model": "T2V-01",
            "prompt": "A cat sitting in a garden"
        }
        
        # Also try with different model names
        model_names = ["T2V-01", "hailuo", "hailuo-2.3", "video-01", "text-to-video"]
        
        for endpoint in video_endpoints:
            print(f"\n🔍 Testing endpoint: {endpoint}")
            
            for model_name in model_names:
                try:
                    test_payload["model"] = model_name
                    response = await client.post(endpoint, json=test_payload)
                    
                    print(f"   Model {model_name}: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ SUCCESS! Endpoint: {endpoint}, Model: {model_name}")
                        print(f"   Response: {data}")
                        return endpoint, model_name
                        
                    elif response.status_code == 400:
                        error_text = response.text
                        if "unknown model" not in error_text.lower():
                            print(f"   ⚠️ Different error: {error_text[:100]}...")
                        
                    elif response.status_code not in [404, 405]:
                        print(f"   ⚠️ Status {response.status_code}: {response.text[:100]}...")
                        break  # Don't try other models for this endpoint
                
                except Exception as e:
                    print(f"   ❌ Error with {model_name}: {e}")
                    
        print(f"\n❌ No working video endpoint found")
        return None, None

if __name__ == "__main__":
    endpoint, model = asyncio.run(test_video_endpoints())
    if endpoint and model:
        print(f"\n🎉 Found working video: {endpoint} with model {model}")
    else:
        print(f"\n💭 No working video generation found")
    sys.exit(0 if endpoint else 1)