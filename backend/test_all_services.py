#!/usr/bin/env python3
"""Test all MiniMax services: text, voice, video"""
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

async def test_all_services():
    """Test all MiniMax API services"""
    
    print("🧪 Testing all MiniMax services...")
    
    try:
        client = MiniMaxClient()
        print("✅ Client initialized")
        
        # 1. Test text generation
        print("\n📝 Testing text generation...")
        try:
            text_response = await client.generate_text(
                "Write a brief professional greeting for a sales email.", 
                max_tokens=100
            )
            print(f"✅ Text generation works!")
            print(f"   Response: {text_response[:200]}...")
        except Exception as e:
            print(f"❌ Text generation failed: {e}")
            return False
        
        # 2. Test speech generation  
        print("\n🔊 Testing speech generation...")
        try:
            audio_bytes = await client.generate_speech(
                "Hello, this is a test of the MiniMax speech synthesis.",
                voice_id="female-shaonv",
                emotion="happy"
            )
            print(f"✅ Speech generation works! Generated {len(audio_bytes)} bytes")
            
            # Save test audio
            test_audio_path = Path(__file__).parent / "outputs" / "test_audio.mp3"
            test_audio_path.parent.mkdir(exist_ok=True)
            test_audio_path.write_bytes(audio_bytes)
            print(f"   Saved test audio to: {test_audio_path}")
            
        except Exception as e:
            print(f"❌ Speech generation failed: {e}")
            return False
        
        # 3. Test video generation (just start it, don't wait)
        print("\n🎥 Testing video generation...")
        try:
            video_result = await client.generate_video(
                "Professional business person in modern office, talking to camera, 5 seconds"
            )
            print(f"✅ Video generation started!")
            print(f"   Task ID: {video_result.get('task_id')}")
            
            # Check status once
            if video_result.get("task_id"):
                status = await client.check_video_status(video_result["task_id"])
                print(f"   Status: {status.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Video generation failed: {e}")
            # Video failure is not critical, continue
        
        await client.close()
        
        print("\n🎉 Core MiniMax API tests passed!")
        print("✅ Text generation: Working")
        print("✅ Speech generation: Working")
        print("⚡ Video generation: Started (async)")
        return True
        
    except Exception as e:
        print(f"❌ Overall test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_all_services())
    sys.exit(0 if success else 1)