#!/usr/bin/env python3
"""
Test script for optimized prompts
Run with: python test_prompts.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from services.minimax import get_client

# Sample test data
SAMPLE_COMPANY_DATA = {
    "healthcare": {
        "url": "https://medflowhealth.com",
        "content": """MedFlow Regional Health - About Us
        
        We are a comprehensive healthcare provider serving the tri-state area with 12 locations. 
        Our team of 45 physicians and 120 support staff provide primary care, cardiology, 
        orthopedics, and urgent care services to over 50,000 patients.
        
        Services:
        - Primary Care (Family Medicine, Internal Medicine)
        - Cardiology & Heart Health
        - Orthopedic Surgery & Sports Medicine  
        - Urgent Care (3 locations, open 7 days)
        - Preventive Health Screenings
        
        Recent News:
        - Opened 3 new locations in 2024
        - Implemented Epic EHR system across all practices
        - Awarded "Best Regional Healthcare Provider" 2024
        
        Patient Portal: Schedule appointments, view test results, request prescription refills
        Insurance: We accept most major insurance plans
        
        Locations: Albany, Troy, Schenectady, plus 9 suburban locations
        
        Contact: (518) 555-0123 | info@medflowhealth.com
        """
    },
    "legal": {
        "url": "https://morrisonlaw.com", 
        "content": """Morrison & Associates - Premier M&A Legal Services
        
        Leading regional law firm specializing in mergers & acquisitions, corporate law, 
        and business transactions. 25 attorneys, 40 support staff.
        
        Practice Areas:
        - Mergers & Acquisitions (70% of practice)
        - Corporate Law & Securities
        - Business Litigation
        - Employment Law
        - Real Estate Transactions
        
        Recent Highlights:
        - Advised on $2.3B healthcare merger (2024)
        - Completed 47 M&A transactions in 2023
        - Expanded corporate practice with 5 new senior associates
        - Named "Regional M&A Firm of the Year" by Legal 500
        
        Clients: Mid-market companies ($10M-500M revenue), private equity firms, 
        family offices, public companies
        
        Notable Transactions:
        - $450M software company acquisition
        - $180M manufacturing divestiture
        - Cross-border transactions in healthcare, technology, manufacturing
        """
    },
    "manufacturing": {
        "url": "https://precisionmfg.com",
        "content": """Precision Manufacturing Solutions - Advanced Components
        
        ISO 9001:2015 certified manufacturer of precision machined components for 
        aerospace, medical device, and automotive industries. 
        
        Capabilities:
        - CNC Machining (5-axis, Swiss)
        - Quality Control & Inspection
        - Assembly & Testing
        - Design Engineering Support
        
        Facility: 85,000 sq ft, 120 employees
        Equipment: 45 CNC machines, coordinate measuring machines, clean room assembly
        
        Recent Growth:
        - Added 4 new product lines in 18 months
        - Increased capacity by 40% in 2024
        - New aerospace contracts worth $15M annually
        - Implementing lean manufacturing initiatives
        
        Quality Standards: AS9100D (aerospace), ISO 13485 (medical)
        Certifications: ITAR registered, FDA registered
        
        Industries Served:
        - Aerospace & Defense (40%)
        - Medical Devices (35%) 
        - Automotive (20%)
        - Industrial Equipment (5%)
        """
    }
}

async def test_research_prompt(company_data, prompt_file="backend/prompts/research_optimized.txt"):
    """Test the research prompt with sample company data"""
    print(f"\n🔍 TESTING RESEARCH PROMPT - {company_data['url']}")
    print("="*60)
    
    # Load prompt
    with open(prompt_file, 'r') as f:
        prompt_template = f.read()
    
    # Fill in the prompt
    filled_prompt = prompt_template.format(
        url=company_data['url'],
        content=company_data['content']
    )
    
    print(f"Prompt length: {len(filled_prompt)} characters")
    
    try:
        # Get AI response
        client = get_client()
        response = await client.generate_text(filled_prompt, max_tokens=2000)
        
        print(f"Response length: {len(response)} characters")
        print("\nRAW RESPONSE:")
        print("-" * 30)
        print(response[:500] + "..." if len(response) > 500 else response)
        
        # Try to parse as JSON
        try:
            # Clean up potential markdown
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split('\n')
                clean_response = '\n'.join(lines[1:-1])
            
            parsed = json.loads(clean_response)
            print("\n✅ JSON PARSING: SUCCESS")
            print(f"Company: {parsed.get('company_name', 'N/A')}")
            print(f"Industry: {parsed.get('industry', 'N/A')}")
            print(f"Size: {parsed.get('company_size', 'N/A')}")
            print(f"Pain Points: {len(parsed.get('pain_points', []))}")
            print(f"Decision Makers: {len(parsed.get('key_decision_makers', []))}")
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON PARSING FAILED: {e}")
            return None
            
    except Exception as e:
        print(f"❌ API ERROR: {e}")
        return None

async def test_script_prompt(research_data, prompt_file="backend/prompts/script_optimized.txt"):
    """Test the script prompt with research data"""
    print(f"\n🎬 TESTING SCRIPT PROMPT")
    print("="*60)
    
    if not research_data:
        print("❌ No research data to test script generation")
        return None
    
    # Load prompt
    with open(prompt_file, 'r') as f:
        prompt_template = f.read()
    
    # Fill in the prompt
    filled_prompt = prompt_template.format(
        research=json.dumps(research_data, indent=2),
        our_product="Custom AI agent development and automation consulting for enterprise clients"
    )
    
    print(f"Prompt length: {len(filled_prompt)} characters")
    
    try:
        client = get_client()
        response = await client.generate_text(filled_prompt, max_tokens=1000)
        
        print(f"Response length: {len(response)} characters")
        print("\nGENERATED SCRIPT:")
        print("-" * 30)
        print(response)
        
        # Count words
        word_count = len(response.split())
        print(f"\n📊 WORD COUNT: {word_count}")
        
        if 75 <= word_count <= 150:
            print("✅ Word count is within target range (75-150)")
        else:
            print("⚠️  Word count outside target range")
        
        # Check for company name
        company_name = research_data.get('company_name', '')
        if company_name.lower() in response.lower():
            print(f"✅ Company name '{company_name}' found in script")
        else:
            print(f"⚠️  Company name '{company_name}' not found in script")
        
        return response
        
    except Exception as e:
        print(f"❌ API ERROR: {e}")
        return None

async def test_video_prompt(script_data, industry, prompt_file="backend/prompts/video_optimized.txt"):
    """Test the video prompt with script data"""
    print(f"\n🎥 TESTING VIDEO PROMPT")
    print("="*60)
    
    if not script_data:
        print("❌ No script data to test video generation")
        return None
        
    # Load prompt
    with open(prompt_file, 'r') as f:
        prompt_template = f.read()
    
    # Fill in the prompt
    filled_prompt = prompt_template.format(
        script=script_data,
        industry=industry,
        company_overview="Sample company overview",
        mood="professional, innovative, trustworthy"
    )
    
    print(f"Prompt length: {len(filled_prompt)} characters")
    
    try:
        client = get_client()
        response = await client.generate_text(filled_prompt, max_tokens=1500)
        
        print(f"Response length: {len(response)} characters")
        print("\nGENERATED VIDEO PROMPT:")
        print("-" * 30)
        print(response[:800] + "..." if len(response) > 800 else response)
        
        # Check for key elements
        required_elements = ["MAIN PROMPT:", "STYLE MODIFIERS:", "NEGATIVE PROMPT:", "DURATION:", "ASPECT RATIO:"]
        missing_elements = []
        
        for element in required_elements:
            if element not in response:
                missing_elements.append(element)
        
        if not missing_elements:
            print("✅ All required video prompt elements present")
        else:
            print(f"⚠️  Missing elements: {missing_elements}")
        
        return response
        
    except Exception as e:
        print(f"❌ API ERROR: {e}")
        return None

async def run_comprehensive_test():
    """Run tests on all sample companies"""
    print("🚀 STARTING COMPREHENSIVE PROMPT TESTING")
    print("=" * 80)
    
    results = {}
    
    for industry, company_data in SAMPLE_COMPANY_DATA.items():
        print(f"\n{'='*20} TESTING {industry.upper()} {'='*20}")
        
        # Test research prompt
        research_result = await test_research_prompt(company_data)
        
        # Test script prompt (if research succeeded)
        script_result = await test_script_prompt(research_result) if research_result else None
        
        # Test video prompt (if script succeeded)
        video_result = await test_video_prompt(script_result, industry) if script_result else None
        
        results[industry] = {
            "research": research_result is not None,
            "script": script_result is not None,
            "video": video_result is not None,
            "research_data": research_result,
            "script_data": script_result,
            "video_data": video_result
        }
        
        # Brief delay between tests
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n{'='*20} TEST SUMMARY {'='*20}")
    for industry, result in results.items():
        print(f"{industry.upper():15} | Research: {'✅' if result['research'] else '❌'} | Script: {'✅' if result['script'] else '❌'} | Video: {'✅' if result['video'] else '❌'}")
    
    return results

async def main():
    """Main test function"""
    # Check if API key is set
    if not os.getenv("MINIMAX_API_KEY"):
        print("❌ MINIMAX_API_KEY environment variable not set")
        print("Set it with: export MINIMAX_API_KEY='your-key-here'")
        return
    
    try:
        await run_comprehensive_test()
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
    finally:
        # Clean up client
        client = get_client()
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())