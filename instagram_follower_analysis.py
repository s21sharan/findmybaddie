import json
import argparse
import pandas as pd
import re
import unicodedata
import os
from collections import defaultdict
import requests
from pathlib import Path
import time
import importlib.util

def load_json_data(file_path):
    """Load JSON data from file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def extract_follower_names(data):
    """Extract follower names from the Instagram JSON data structure"""
    followers = []
    
    # Check if we have a proper structure with related_profiles
    if 'node' in data and 'edge_related_profiles' in data['node']:
        related_profiles = data['node']['edge_related_profiles']['edges']
        
        for profile in related_profiles:
            if 'node' in profile:
                username = profile['node'].get('username', '')
                full_name = profile['node'].get('full_name', '')
                
                # Get profile picture URL if available
                profile_pic_url = profile['node'].get('profile_pic_url', '')
                
                followers.append({
                    'username': username,
                    'full_name': full_name,
                    'profile_pic_url': profile_pic_url
                })
    
    return followers

def normalize_name(name):
    """Normalize name by removing emojis and special characters"""
    # Remove emojis and other special characters
    name = ''.join(c for c in name if c.isalpha() or c.isspace())
    # Normalize unicode characters
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return name.strip()

def is_human_name(name):
    """Check if a name appears to be a human name rather than an organization or business"""
    # Normalize and lowercase the name
    norm_name = normalize_name(name).lower()
    
    # List of keywords that indicate non-human entities
    non_human_keywords = [
        'ucla', 'store', 'club', 'official', 'university', 'association', 'group',
        'organization', 'school', 'community', 'foundation', 'society', 'team',
        'committee', 'company', 'inc', 'corp', 'llc', 'association', 'the',
        'enabler', 'athletics', 'admission', 'engineering', 'barstool', 'school',
        'den', 'backpacking', 'sjp', 'shop', 'tuned', 'metronome', 'samueli', 
        'undergraduate', 'what\'s bruin', 'berkeley', 'official'
    ]
    
    # Check for keywords indicating an organization/business
    for keyword in non_human_keywords:
        if keyword in norm_name.split():
            return False
    
    # Check if the name is in all uppercase (common for organizations)
    if name.isupper() and len(name) > 3:
        return False
        
    # If we passed all checks, it's likely a human name
    return True

def analyze_with_perplexity_bulk(followers, api_key):
    """Use Perplexity API to analyze gender and ethnicity in a single batch to minimize API usage"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    url = "https://api.perplexity.ai/chat/completions"
    
    # Prepare data for all followers in one batch
    followers_data = []
    for i, person in enumerate(followers):
        followers_data.append({
            "id": i,
            "username": person.get('username', ''),
            "full_name": person.get('full_name', '')
        })
    
    # Create a concise JSON prompt with all profiles
    followers_json = json.dumps(followers_data, ensure_ascii=False)
    
    prompt = f"""Determine gender and ethnicity for these Instagram profiles. Given the size limit, I'll process all at once.

JSON Profiles:
{followers_json}

For EACH profile, determine:
1. Gender (male, female, or unknown)
2. Ethnicity (choose from: east_asian, south_asian, hispanic, black, middle_eastern, white, other, or unknown)

Return a JSON array with results in this exact format, with one object per profile:
[
  {{
    "id": 0,
    "gender": "female",
    "ethnicity": "white",
    "confidence": "high"
  }},
  ...etc for all profiles
]

Be concise. Format must be parseable JSON without extra text."""

    print(f"Analyzing {len(followers)} profiles in a single API call...")
    
    try:
        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": "You are an expert in determining gender and ethnicity from names. Respond only with the requested JSON format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 4000
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            response_data = response.json()
            result_text = response_data["choices"][0]["message"]["content"]
            
            # Extract JSON data
            try:
                # Clean up the response if needed
                result_text = result_text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]  # Remove ```json and ```
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]  # Remove ``` and ```
                    
                # Parse the results
                analysis_results = json.loads(result_text)
                
                # Create a lookup by ID
                results_by_id = {item.get('id'): item for item in analysis_results}
                
                # Apply results back to original follower data
                for i, person in enumerate(followers):
                    if i in results_by_id:
                        result = results_by_id[i]
                        person['predicted_gender'] = result.get('gender', 'unknown')
                        person['predicted_race'] = result.get('ethnicity', 'unknown')
                        person['confidence'] = result.get('confidence', 'low')
                        person['analysis_source'] = 'perplexity'
                    else:
                        person['predicted_gender'] = 'unknown'
                        person['predicted_race'] = 'unknown'
                        person['confidence'] = 'none'
                        person['analysis_source'] = 'error'
                
                print(f"Successfully analyzed {len(results_by_id)} profiles")
                
            except json.JSONDecodeError as e:
                print(f"Error parsing Perplexity response: {e}")
                print(f"Raw response: {result_text}")
                # Mark all as unknown
                for person in followers:
                    person['predicted_gender'] = 'unknown'
                    person['predicted_race'] = 'unknown'
                    person['analysis_source'] = 'error'
        else:
            print(f"API error: {response.status_code}")
            print(f"Response: {response.text}")
            # Mark all as unknown
            for person in followers:
                person['predicted_gender'] = 'unknown'
                person['predicted_race'] = 'unknown'
                person['analysis_source'] = 'error'
    
    except Exception as e:
        print(f"Exception during API call: {e}")
        # Mark all as unknown
        for person in followers:
            person['predicted_gender'] = 'unknown'
            person['predicted_race'] = 'unknown'
            person['analysis_source'] = 'error'
    
    return followers

def load_api_key():
    """Attempt to load the Perplexity API key from api_config.py"""
    try:
        # Try to import api_config module
        spec = importlib.util.spec_from_file_location("api_config", "api_config.py")
        if spec and spec.loader:
            api_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(api_config)
            return getattr(api_config, "PERPLEXITY_API_KEY", "")
        return ""
    except (ImportError, FileNotFoundError):
        print("api_config.py not found or couldn't be imported")
        return ""

def main():
    parser = argparse.ArgumentParser(description='Analyze Instagram followers from JSON data')
    parser.add_argument('--input', '-i', required=True, help='Path to JSON file with Instagram data')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--human-only', action='store_true', help='Filter out non-human accounts')
    parser.add_argument('--api-key', help='Perplexity API key')
    
    args = parser.parse_args()
    
    # Get API key from args, environment, or config file
    api_key = args.api_key or os.environ.get("PERPLEXITY_API_KEY", "") or load_api_key()
    
    if not api_key:
        print("Warning: No Perplexity API key found. Please provide one via --api-key argument, PERPLEXITY_API_KEY environment variable, or in api_config.py")
    
    # Load data
    print(f"Loading data from {args.input}...")
    data = load_json_data(args.input)
    
    # Extract follower names
    print("Extracting follower names...")
    followers = extract_follower_names(data)
    print(f"Found {len(followers)} follower profiles")
    
    # Filter for human accounts if requested
    if args.human_only:
        print("Filtering for human accounts...")
        human_followers = [f for f in followers if is_human_name(f['full_name'])]
        print(f"Filtered to {len(human_followers)} human accounts (removed {len(followers) - len(human_followers)} non-human accounts)")
        followers = human_followers
    
    # Analyze with Perplexity if API key is provided
    if api_key:
        print("Analyzing profiles with Perplexity API...")
        followers = analyze_with_perplexity_bulk(followers, api_key)
    else:
        print("No Perplexity API key provided. Unable to analyze profiles.")
        
    # Display results
    print("\nResults:")
    for follower in followers:
        gender_info = follower.get('predicted_gender', 'unknown')
        ethnicity = follower.get('predicted_race', 'unknown')
        confidence = follower.get('confidence', 'unknown')
        username = follower.get('username', '')
        full_name = follower.get('full_name', '')
        
        print(f"{username} ({full_name}) - Gender: {gender_info}, Ethnicity: {ethnicity} (Confidence: {confidence})")
    
    # Save to output file if specified
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(followers, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main() 