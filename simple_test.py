#!/usr/bin/env python3
"""Simple test script for debugging prompt issues"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Simple company data
SAMPLE_DATA = """
MedFlow Regional Health - About Us

We are a comprehensive healthcare provider serving the tri-state area with 12 locations. 
Our team of 45 physicians and 120 support staff provide primary care, cardiology, 
orthopedics, and urgent care services to over 50,000 patients.

Services:
- Primary Care (Family Medicine, Internal Medicine)  
- Cardiology & Heart Health
- Urgent Care (3 locations, open 7 days)

Recent News:
- Opened 3 new locations in 2024
- Implemented Epic EHR system across all practices

Contact: (518) 555-0123 | info@medflowhealth.com
"""

async def test_research_simple():
    """Simple test of research prompt without complex parsing"""
    
    print("🔍 Testing research prompt...")
    
    # Load the optimized prompt
    with open("backend/prompts/research_optimized.txt", 'r') as f:
        prompt_template = f.read()
    
    # Fill in the template using replace instead of format
    filled_prompt = prompt_template.replace("{{URL_PLACEHOLDER}}", "https://medflowhealth.com")
    filled_prompt = filled_prompt.replace("{{CONTENT_PLACEHOLDER}}", SAMPLE_DATA)
    
    print(f"Prompt length: {len(filled_prompt)} characters")
    
    try:
        from services.minimax import get_client
        client = get_client()
        
        print("Calling MiniMax API...")
        response = await client.generate_text(filled_prompt, max_tokens=2000)
        
        print(f"Response length: {len(response)} characters")
        print("\nFirst 500 characters of response:")
        print("=" * 50)
        print(response[:500])
        print("=" * 50)
        
        # Check if response looks like JSON
        if response.strip().startswith('{'):
            print("✅ Response appears to be JSON format")
        else:
            print("⚠️  Response doesn't appear to be JSON")
            
        await client.close()
        return response
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def main():
    if not os.getenv("MINIMAX_API_KEY"):
        print("❌ MINIMAX_API_KEY not set")
        return
        
    await test_research_simple()

if __name__ == "__main__":
    asyncio.run(main())