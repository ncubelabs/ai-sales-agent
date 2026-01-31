#!/usr/bin/env python3
"""Test MiniMax API connection"""
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

async def test_minimax():
    """Test all MiniMax API endpoints"""
    
    print("🧪 Testing MiniMax API connection...")
    
    # Check API key
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("❌ ERROR: MINIMAX_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key loaded: {api_key[:10]}...")
    
    try:
        # Initialize client
        client = MiniMaxClient()
        print("✅ Client initialized")
        
        # Test text generation (M2.1)
        print("\n📝 Testing text generation...")
        try:
            # First let's try to understand what endpoints exist
            print("   Trying direct HTTP request to understand API...")
            payload = {
                "model": "abab6.5s-chat",
                "messages": [{"role": "user", "content": "Hello, test message"}],
                "max_tokens": 100
            }
            
            response = await client.http_client.post("/chat/completions", json=payload)
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                print(f"   Response body: {response.text}")
                # Try different model names
                model_names = [
                    "abab6.5-chat", "abab6.5s", "abab6", "minimax",
                    "abab6.5s-chat", "abab6.5-s-chat", "abab7-chat",
                    "abab5.5-chat", "abab5.5s-chat", "text-abab6.5s-chat",
                    "abab6.5s-text", "gpt-3.5-turbo", "abab6.5g-chat"
                ]
                for model_name in model_names:
                    print(f"   Trying model: {model_name}")
                    payload["model"] = model_name
                    try:
                        resp = await client.http_client.post("/chat/completions", json=payload)
                        if resp.status_code == 200:
                            print(f"   ✅ Model {model_name} works!")
                            result_data = resp.json()
                            result = result_data["choices"][0]["message"]["content"]
                            print(f"   Response: {result[:100]}...")
                            working_model = model_name
                            break
                        else:
                            print(f"   ❌ Model {model_name} failed: {resp.status_code}")
                            if resp.status_code == 400:
                                error_text = resp.text
                                if "unknown model" in error_text:
                                    continue  # Try next model
                                else:
                                    print(f"      Different error: {error_text}")
                    except Exception as e:
                        print(f"   ❌ Model {model_name} error: {e}")
                
                if 'working_model' not in locals():
                    print("   No working model found, trying to get available models...")
                    # Try to get a list of available models
                    try:
                        models_resp = await client.http_client.get("/models")
                        print(f"   Models endpoint status: {models_resp.status_code}")
                        if models_resp.status_code == 200:
                            models_data = models_resp.json()
                            print(f"   Available models: {models_data}")
                    except Exception as e:
                        print(f"   Models endpoint error: {e}")
                else:
                    print(f"✅ Found working model: {working_model}")
            
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"]
            print(f"✅ Text generation works!")
            print(f"   Response: {result[:100]}...")
        except Exception as e:
            print(f"❌ Text generation failed: {e}")
            return False
        
        # Test speech generation
        print("\n🔊 Testing speech generation...")
        try:
            audio_bytes = await client.generate_speech(
                "Hello, this is a test of the MiniMax speech synthesis.",
                voice_id="female-shaonv",
                emotion="happy"
            )
            print(f"✅ Speech generation works! Generated {len(audio_bytes)} bytes")
        except Exception as e:
            print(f"❌ Speech generation failed: {e}")
            return False
        
        # Test video generation (just start, don't wait)
        print("\n🎥 Testing video generation...")
        try:
            video_result = await client.generate_video(
                "Professional business person in modern office, talking to camera"
            )
            print(f"✅ Video generation started!")
            print(f"   Result: {video_result}")
            
            # Check status once
            if video_result.get("task_id"):
                status = await client.check_video_status(video_result["task_id"])
                print(f"   Status check works: {status.get('status')}")
            
        except Exception as e:
            print(f"❌ Video generation failed: {e}")
            return False
        
        await client.close()
        
        print("\n🎉 All MiniMax API tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_minimax())
    sys.exit(0 if success else 1)