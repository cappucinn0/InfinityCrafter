import google.generativeai as genai
import json
import os

CACHE_FILENAME = 'element_cache.json'

class ElementCombiner:
    def __init__(self, api_key, model_name='gemini-2.0-flash'):
        self.api_key = api_key  # Use the passed api_key parameter
        self.model_name = model_name
        self.cache = {}  # Initialize as empty dict, not a set with filename

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

        self.load_cache()

    def load_cache(self):
        try:
            if os.path.exists("element_cache.json"):
                with open("element_cache.json", 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # Check if file has content
                        self.cache = json.loads(content)
                    else:
                        self.cache = {}
            else:
                self.cache = {}
                print("Cache file not found. Starting with empty cache.")
        except json.JSONDecodeError:
            print("Cache file corrupted. Starting with empty cache.")
            self.cache = {}
        except Exception as e:
            print(f"Error loading cache: {e}")
            self.cache = {}

    def save_cache(self):
        try:
            with open("element_cache.json", 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            print(f"Cache saved with {len(self.cache)} entries")
        except Exception as e:
            print(f"Error saving cache: {e}")

    def make_cache_key(self, el1, el2):
        # Remove emojis for consistent key generation
        def clean_element(element):
            # Remove common emojis and strip whitespace
            import re
            # Remove emojis using regex
            emoji_pattern = re.compile("["
                                       u"\U0001F600-\U0001F64F"  # emoticons
                                       u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                       u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                       u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                       u"\U00002702-\U000027B0"
                                       u"\U000024C2-\U0001F251"
                                       "]+", flags=re.UNICODE)
            return emoji_pattern.sub('', element).strip()
        
        clean_el1 = clean_element(el1).lower()
        clean_el2 = clean_element(el2).lower()
        return '+'.join(sorted([clean_el1, clean_el2]))

    def call_gemini_api(self, el1, el2):
        key = self.make_cache_key(el1, el2)
        
        # Check cache first
        if key in self.cache:
            print(f"Cache hit for {el1} + {el2}: {self.cache[key]}")
            return self.cache[key]

        print(f"Cache miss for {el1} + {el2}. Calling Gemini API...")
        
        # Compose prompt for Gemini
        prompt = f"""
You are an expert in element combinations similar to Little Alchemy. When given two element names, output only the emoji followed by the element name formed by combining them.

If you are not exactly sure, give the closest possible element you think fits best. Similar elements when combined can have the same outputs, so do not worry about multiple valid answers.

Examples:
Input: Fire + Water
Output: 💨Steam

Input: Earth + Air
Output: 🌪️Dust

Input: Water + Earth
Output: 🌱Mud

Make sure to Always output an emoji followed by the element name with NO SPACES between them, like this: "🔥Firestorm". Make sure the emojis are unique and make sense

Reply only in English.

Try to be as logical as possible and be open to creative combinations with creative products.

Here are some more examples that you can learn from:

"earth+earth": "🏞️Land",
"land+land": "🗺️Continent",
"continent+continent": "🌍Planet",
"planet+planet": "☀️Solar System",
"solar system+solar system": "🌌Galaxy",
"galaxy+galaxy": "🌀Universe",

"water+water": "💦Puddle",
"puddle+puddle": "🏞️Lake",
"lake+lake": "🌊Ocean",
"ocean+ocean": "🌪️Pressure",
"pressure+pressure": "🧽Deep Sea",
"deep sea+deep sea": "🐙Abyss",

"fire+fire": "🔥Energy",
"energy+energy": "⚡Lightning",
"lightning+fire": "💥Explosion",
"explosion+energy": "🚀Rocket",
"rocket+rocket": "🛰️Satellite",
"satellite+energy": "🌠Star",
"star+star": "🌞Sun",

"air+air": "💨Wind",
"wind+wind": "🌪️Tornado",
"tornado+wind": "🌀Storm",
"storm+air": "☁️Cloud",
"cloud+cloud": "⛈️Thunderstorm",
"thunderstorm+storm": "🌫️Atmosphere",
"atmosphere+air": "🌈Sky",

"life+life": "🧫Cell",
"cell+cell": "🦠Organism",
"organism+organism": "🐒Animal",
"animal+intelligence": "🧍Human",
"human+human": "🏘️Society",
"society+knowledge": "🏛️Civilization",
"civilization+time": "🚀Future"

Input: {el1} + {el2}
Output: 

"""

        try:
            response = self.model.generate_content(prompt)
            output = response.text.strip()
            
            # Cache the result
            self.cache[key] = output
            self.save_cache()
            
            print(f"API result for {el1} + {el2}: {output}")
            return output
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return f"❓Unknown"  # Return a default combination

    def combine_elements(self, el1, el2):
        """Alternative method name for compatibility"""
        return self.call_gemini_api(el1, el2)