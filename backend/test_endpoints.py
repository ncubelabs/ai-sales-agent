#!/usr/bin/env python3
"""Test all backend API endpoints"""
import asyncio
import httpx
import json
import time
from pathlib import Path

async def test_all_endpoints():
    """Test all API endpoints"""
    
    base_url = "http://localhost:8000"
    print(f"🧪 Testing API endpoints at {base_url}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # 1. Test health endpoint
        print(f"\n🏥 Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Health check passed: {response.json()}")
            else:
                print(f"   ❌ Health check failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Health endpoint error: {e}")
            return False
        
        # 2. Test root endpoint
        print(f"\n📋 Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Root endpoint works")
                print(f"   Endpoints: {list(data.get('endpoints', {}).keys())}")
            else:
                print(f"   ❌ Root endpoint failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Root endpoint error: {e}")
        
        # 3. Test research endpoint
        print(f"\n🔍 Testing research endpoint...")
        try:
            research_payload = {
                "url": "https://www.openai.com",
                "deep_scrape": False
            }
            response = await client.post(f"{base_url}/api/research", json=research_payload)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Research endpoint works")
                print(f"   Company: {data.get('company_name', 'Unknown')}")
                print(f"   Industry: {data.get('industry', 'Unknown')}")
                research_data = data  # Save for next test
            else:
                print(f"   ❌ Research failed: {response.text}")
                research_data = {
                    "company_name": "Test Company",
                    "industry": "Technology",
                    "products_services": ["AI solutions"],
                    "value_proposition": "Advanced AI technology",
                    "target_audience": "Businesses",
                    "pain_points": ["Efficiency"],
                    "recent_news": [],
                    "company_size": "Medium",
                    "tone": "professional",
                    "key_decision_makers": ["CTO"],
                    "personalization_hooks": ["AI adoption"]
                }
        except Exception as e:
            print(f"   ❌ Research endpoint error: {e}")
            research_data = {
                "company_name": "Test Company",
                "industry": "Technology",
                "products_services": ["AI solutions"],
                "value_proposition": "Advanced AI technology",
                "target_audience": "Businesses", 
                "pain_points": ["Efficiency"],
                "recent_news": [],
                "company_size": "Medium",
                "tone": "professional",
                "key_decision_makers": ["CTO"],
                "personalization_hooks": ["AI adoption"]
            }
        
        # 4. Test script endpoint
        print(f"\n📝 Testing script generation...")
        try:
            script_payload = {
                "research": research_data,
                "our_product": "AI-powered sales automation platform",
                "max_words": 100
            }
            response = await client.post(f"{base_url}/api/script", json=script_payload)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Script generation works")
                print(f"   Word count: {data.get('word_count', 0)}")
                print(f"   Script preview: {data.get('script', '')[:100]}...")
                script_text = data.get('script', 'Hello, this is a test script.')
            else:
                print(f"   ❌ Script generation failed: {response.text}")
                script_text = "Hello, this is a test script for voice generation."
        except Exception as e:
            print(f"   ❌ Script endpoint error: {e}")
            script_text = "Hello, this is a test script for voice generation."
        
        # 5. Test voice endpoint
        print(f"\n🔊 Testing voice generation...")
        try:
            voice_payload = {
                "text": script_text[:100],  # Limit to avoid long generation
                "voice_id": "female-shaonv",
                "emotion": "happy"
            }
            response = await client.post(f"{base_url}/api/voice", json=voice_payload)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Voice generation works")
                print(f"   Audio file: {data.get('audio_path', 'Unknown')}")
                print(f"   File size: {data.get('file_size', 0)} bytes")
            else:
                print(f"   ❌ Voice generation failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Voice endpoint error: {e}")
        
        # 6. Test video endpoint (will likely fail but should handle gracefully)
        print(f"\n🎥 Testing video generation...")
        try:
            video_payload = {
                "prompt": "Professional person in modern office, 5 seconds",
                "model": "T2V-01"
            }
            response = await client.post(f"{base_url}/api/video", json=video_payload)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Video generation started")
                print(f"   Job ID: {data.get('job_id', 'Unknown')}")
                job_id = data.get('job_id')
                
                # Check status
                if job_id:
                    status_response = await client.get(f"{base_url}/api/status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"   Status: {status_data.get('status', 'unknown')}")
            else:
                print(f"   ⚠️ Video generation failed (expected): {response.text}")
        except Exception as e:
            print(f"   ⚠️ Video endpoint error (expected): {e}")
        
        # 7. Test full generation pipeline (skip video for speed)
        print(f"\n🚀 Testing full generation pipeline...")
        try:
            generate_payload = {
                "company_url": "https://www.anthropic.com",
                "our_product": "AI sales automation",
                "skip_video": True  # Skip video for faster testing
            }
            response = await client.post(f"{base_url}/api/generate", json=generate_payload)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Full pipeline started")
                print(f"   Job ID: {data.get('job_id', 'Unknown')}")
                job_id = data.get('job_id')
                
                # Poll status a few times
                if job_id:
                    for i in range(3):
                        await asyncio.sleep(2)
                        status_response = await client.get(f"{base_url}/api/generate/status/{job_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status', 'unknown')
                            progress = status_data.get('progress', 0)
                            print(f"   Poll {i+1}: {status} ({progress}%)")
                            if status in ['completed', 'failed']:
                                break
            else:
                print(f"   ❌ Full pipeline failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Generate endpoint error: {e}")
    
    print(f"\n🎉 Endpoint testing complete!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_all_endpoints())
    print(f"\n{'✅ All tests completed!' if success else '❌ Some tests failed'}")