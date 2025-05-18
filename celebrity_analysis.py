import requests
import json
import re
from typing import Dict, Any
from bs4 import BeautifulSoup

class CelebrityAnalyzer:
    def __init__(self):
        self.wiki_api_url = "https://en.wikipedia.org/w/api.php"
        
    def get_celebrity_info(self, celebrity_name: str) -> Dict[str, Any]:
        """Get comprehensive information about a celebrity using Wikipedia"""
        info = {
            "name": celebrity_name,
            "sex": self._get_sex(celebrity_name),
            "race": self._get_race(celebrity_name),
        }
        return info
    
    def _get_page_content(self, celebrity_name: str) -> str:
        """Get Wikipedia page content for a celebrity"""
        # Get the page ID
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": celebrity_name,
            "utf8": 1
        }
        
        try:
            response = requests.get(self.wiki_api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "query" in data and "search" in data["query"] and data["query"]["search"]:
                page_title = data["query"]["search"][0]["title"]
                
                # Get the page content - full page to better detect race
                params = {
                    "action": "parse",
                    "format": "json",
                    "page": page_title,
                    "prop": "text",
                    "utf8": 1
                }
                
                response = requests.get(self.wiki_api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "parse" in data and "text" in data["parse"]:
                    html_content = data["parse"]["text"]["*"]
                    # Parse HTML to plain text
                    soup = BeautifulSoup(html_content, "html.parser")
                    return soup.get_text()
            
            return f"No Wikipedia information found for {celebrity_name}"
        
        except Exception as e:
            print(f"Error fetching Wikipedia data for {celebrity_name}: {e}")
            return f"Error fetching information for {celebrity_name}"
    
    def _get_sex(self, celebrity_name: str) -> str:
        """Guess sex/gender information about the celebrity"""
        content = self._get_page_content(celebrity_name)
        
        # Simple heuristic looking for pronouns
        he_count = len(re.findall(r'\bhe\b|\bhis\b|\bhim\b', content.lower()))
        she_count = len(re.findall(r'\bshe\b|\bher\b|\bhers\b', content.lower()))
        
        if he_count > she_count:
            return "Male"
        elif she_count > he_count:
            return "Female"
        else:
            return "Unknown"
    
    def _get_race(self, celebrity_name: str) -> str:
        """Try to determine race/ethnicity information with improved detection"""
        content = self._get_page_content(celebrity_name)
        
        # Enhanced keywords for race/ethnicity detection
        keywords = {
            "African American/Black": [
                "african american", "african-american", "black american", "black", 
                "african descent", "nigerian", "kenyan", "jamaican", "haitian"
            ],
            "White/Caucasian": [
                "caucasian", "white american", "european american", "white", 
                "irish", "italian", "german", "english", "scottish", "french"
            ],
            "Hispanic/Latino": [
                "hispanic", "latino", "latina", "latinx", "mexican", "puerto rican",
                "cuban", "dominican", "spanish", "colombian", "venezuelan"
            ],
            "Asian": [
                "asian", "chinese", "japanese", "korean", "vietnamese", "filipino",
                "indian", "pakistani", "bangladeshi", "thai", "cambodian"
            ],
            "Mixed Race": [
                "mixed race", "biracial", "multiracial", "mixed heritage"
            ],
            "Native American": [
                "native american", "indigenous", "american indian", "cherokee", 
                "navajo", "sioux", "apache"
            ]
        }
        
        # Check for specific race mentions
        for race, terms in keywords.items():
            for term in terms:
                # Use word boundaries to avoid substring matches
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, content.lower()):
                    return race
                
        # Check for "born to" or "parents" context which often mentions ethnicity
        birth_context = re.search(r'born to .{5,100}(family|parents|mother|father)', content.lower())
        if birth_context:
            context = birth_context.group(0).lower()
            for race, terms in keywords.items():
                for term in terms:
                    if term in context:
                        return race
                        
        return "Information not available"

def main():
    # Get input from user for the 3 celebrities
    celebrities_input = input("Enter 3 celebrities that you think are bad (separated by commas): ")
    
    # Split the input by commas and strip whitespace
    bad_celebrities = [name.strip() for name in celebrities_input.split(",")]
    
    # Ensure we have at least one celebrity
    if not bad_celebrities or bad_celebrities[0] == "":
        print("No valid celebrities entered. Using default examples.")
        bad_celebrities = ["Harvey Weinstein", "Amber Heard", "Kanye West"]
    
    # Limit to maximum 3 celebrities if more were entered
    if len(bad_celebrities) > 3:
        print(f"More than 3 celebrities entered. Using only the first 3: {', '.join(bad_celebrities[:3])}")
        bad_celebrities = bad_celebrities[:3]
    
    analyzer = CelebrityAnalyzer()
    
    # Get information for each celebrity
    print("Analyzing celebrities...\n")
    
    for celebrity in bad_celebrities:
        print(f"Getting information about {celebrity}...")
        info = analyzer.get_celebrity_info(celebrity)
        
        print(f"\n{'='*50}\n")
        print(f"CELEBRITY: {celebrity}")
        print(f"{'='*50}")
        print(f"Sex: {info['sex']}")
        print(f"Race: {info['race']}")
        print(f"\n{'-'*50}\n")

if __name__ == "__main__":
    main() 