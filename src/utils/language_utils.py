"""
Language Detection and Translation Utilities
Supports Norwegian (Bokmål) and English
"""

import re
from typing import Dict, Tuple, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


class LanguageDetector:
    """Detect language of input text"""
    
    # Norwegian-specific words (common in financial contexts)
    NORWEGIAN_INDICATORS = {
        'hvor', 'mye', 'hva', 'bruker', 'nordmenn', 'norske', 
        'familier', 'hushold', 'utgifter', 'kostnader', 'månedlig',
        'gjennomsnittlig', 'budsjettet', 'mat', 'bolig', 'transport',
        'sammenligne', 'mer', 'mindre', 'enn', 'på', 'til', 'og', 'er'
    }
    
    # English-specific patterns
    ENGLISH_INDICATORS = {
        'how', 'much', 'what', 'spend', 'norwegian', 'families',
        'household', 'budget', 'average', 'monthly', 'compare',
        'more', 'less', 'than', 'food', 'housing', 'transport'
    }
    
    def detect(self, text: str) -> str:
        """
        Detect language of text
        
        Returns: 'no' for Norwegian, 'en' for English
        """
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        # Count matches
        no_matches = len(words & self.NORWEGIAN_INDICATORS)
        en_matches = len(words & self.ENGLISH_INDICATORS)
        
        # Norwegian character patterns (æ, ø, å)
        norwegian_chars = len(re.findall(r'[æøå]', text_lower))
        
        # Decision logic
        if norwegian_chars > 0:
            return 'no'
        
        if no_matches > en_matches:
            return 'no'
        elif en_matches > no_matches:
            return 'en'
        else:
            # Default to English if ambiguous
            return 'en'
    
    def is_norwegian(self, text: str) -> bool:
        """Check if text is Norwegian"""
        return self.detect(text) == 'no'
    
    def is_english(self, text: str) -> bool:
        """Check if text is English"""
        return self.detect(text) == 'en'


class BilingualTranslator:
    """Translate between Norwegian and English using local LLM"""
    
    def __init__(self, model_name: str = "llama3.2"):
        self.llm = ChatOllama(model=model_name, temperature=0)
        
        # Translation prompt templates
        self.no_to_en_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional translator specializing in Norwegian to English translation.
Translate the following Norwegian text to English accurately and naturally.
Preserve the meaning and context. Only output the translation, nothing else."""),
            ("user", "{text}")
        ])
        
        self.en_to_no_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional translator specializing in English to Norwegian (Bokmål) translation.
Translate the following English text to Norwegian accurately and naturally.
Preserve the meaning and context. Only output the translation, nothing else."""),
            ("user", "{text}")
        ])
    
    def translate_no_to_en(self, text: str) -> str:
        """Translate Norwegian to English"""
        try:
            chain = self.no_to_en_prompt | self.llm
            response = chain.invoke({"text": text})
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"Translation error (NO→EN): {e}")
            return text  # Return original if translation fails
    
    def translate_en_to_no(self, text: str) -> str:
        """Translate English to Norwegian"""
        try:
            chain = self.en_to_no_prompt | self.llm
            response = chain.invoke({"text": text})
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"Translation error (EN→NO): {e}")
            return text  # Return original if translation fails


class CategoryTranslator:
    """Translate SSB category names between Norwegian and English"""
    
    # SSB COICOP categories (official translations)
    CATEGORIES = {
        '01': {
            'no': 'Mat og alkoholfrie drikkevarer',
            'en': 'Food and non-alcoholic beverages'
        },
        '02': {
            'no': 'Alkoholholdige drikkevarer og tobakk',
            'en': 'Alcoholic beverages and tobacco'
        },
        '03': {
            'no': 'Klær og skotøy',
            'en': 'Clothing and footwear'
        },
        '04': {
            'no': 'Bolig, lys og brensel',
            'en': 'Housing, water, electricity, gas and other fuels'
        },
        '05': {
            'no': 'Møbler, husholdningsartikler og vedlikehold av bolig',
            'en': 'Furnishings, household equipment and routine maintenance'
        },
        '06': {
            'no': 'Helsepleie',
            'en': 'Health'
        },
        '07': {
            'no': 'Transport',
            'en': 'Transport'
        },
        '08': {
            'no': 'Post og telekommunikasjoner',
            'en': 'Communication'
        },
        '09': {
            'no': 'Fritid og kultur',
            'en': 'Recreation and culture'
        },
        '10': {
            'no': 'Undervisning',
            'en': 'Education'
        },
        '11': {
            'no': 'Hotell- og restauranttjenester',
            'en': 'Restaurants and hotels'
        },
        '12': {
            'no': 'Andre varer og tjenester',
            'en': 'Miscellaneous goods and services'
        }
    }
    
    # Simplified category names for matching
    SIMPLE_NAMES = {
        'no': {
            'mat': '01',
            'bolig': '04',
            'transport': '07',
            'klær': '03',
            'helse': '06',
            'fritid': '09',
            'kultur': '09',
            'utdanning': '10',
            'restaurant': '11',
            'alkohol': '02',
            'kommunikasjon': '08',
            'møbler': '05'
        },
        'en': {
            'food': '01',
            'housing': '04',
            'transport': '07',
            'clothing': '03',
            'clothes': '03',
            'health': '06',
            'medical': '06',
            'recreation': '09',
            'entertainment': '09',
            'culture': '09',
            'education': '10',
            'school': '10',
            'restaurants': '11',
            'hotels': '11',
            'alcohol': '02',
            'communication': '08',
            'phone': '08',
            'furniture': '05',
            'furnishings': '05'
        }
    }
    
    def get_category_name(self, code: str, language: str = 'en') -> str:
        """Get category name in specified language"""
        if code in self.CATEGORIES:
            return self.CATEGORIES[code][language]
        return f"Category {code}"
    
    def get_all_categories(self, language: str = 'en') -> Dict[str, str]:
        """Get all categories in specified language"""
        return {code: self.get_category_name(code, language) 
                for code in self.CATEGORIES.keys()}
    
    def match_category(self, text: str, language: str = 'en') -> Optional[str]:
        """Match text to category code"""
        text_lower = text.lower()
        
        # Check simple names
        for name, code in self.SIMPLE_NAMES[language].items():
            if name in text_lower:
                return code
        
        return None


class BilingualPromptBuilder:
    """Build prompts in Norwegian or English"""
    
    SYSTEM_PROMPTS = {
        'en': {
            'baseline': """You are a helpful Norwegian financial assistant.
You have access to Statistics Norway (SSB) household budget data.

When answering questions about Norwegian household spending:
1. Identify the spending category being asked about
2. Provide average spending amount from SSB data
3. Give a clear, helpful answer
4. Always cite Statistics Norway (SSB) as your source

Be concise and cite your sources.""",
            
            'react': """You are a helpful Norwegian financial assistant using Statistics Norway data.

Answer questions using this EXACT format:

THOUGHT: [explain what you need to know]
ACTION: tool_name("argument")
[wait for observation]

Available tools:
- get_spending("category") - get spending for categories like "housing", "food", etc.
- compare_spending("category1", "category2") - compare two categories
- get_total_spending() - get total household spending

After getting observations, provide:
FINAL ANSWER: [your complete answer with sources]

Be concise. Use tools to get data before answering."""
        },
        
        'no': {
            'baseline': """Du er en hjelpsom norsk økonomisk assistent.
Du har tilgang til husholdningsbudsjettdata fra Statistisk sentralbyrå (SSB).

Når du svarer på spørsmål om norske husholdningers utgifter:
1. Identifiser utgiftskategorien som spørres om
2. Oppgi gjennomsnittlig utgift fra SSB-data
3. Gi et klart, nyttig svar
4. Referer alltid til Statistisk sentralbyrå (SSB) som kilde

Vær kortfattet og oppgi kilder.""",
            
            'react': """Du er en hjelpsom norsk økonomisk assistent som bruker data fra Statistisk sentralbyrå.

Svar på spørsmål ved å bruke dette NØYAKTIGE formatet:

TANKE: [forklar hva du trenger å vite]
HANDLING: verktøynavn("argument")
[vent på observasjon]

Tilgjengelige verktøy:
- get_spending("kategori") - hent utgifter for kategorier som "bolig", "mat", etc.
- compare_spending("kategori1", "kategori2") - sammenlign to kategorier
- get_total_spending() - hent totale husholdningsutgifter

Etter å ha mottatt observasjoner, oppgi:
ENDELIG SVAR: [ditt komplette svar med kilder]

Vær kortfattet. Bruk verktøy for å hente data før du svarer."""
        }
    }
    
    @classmethod
    def get_system_prompt(cls, agent_type: str, language: str = 'en') -> str:
        """Get system prompt in specified language"""
        return cls.SYSTEM_PROMPTS[language][agent_type]
    
    @classmethod
    def get_user_prompt(cls, question: str, language: str = 'en') -> str:
        """Format user question"""
        if language == 'no':
            return f"Spørsmål: {question}"
        else:
            return f"Question: {question}"


def test_language_detection():
    """Test language detection"""
    detector = LanguageDetector()
    
    test_cases = [
        ("How much do Norwegian families spend on housing?", "en"),
        ("Hvor mye bruker nordmenn på bolig?", "no"),
        ("What is the average food budget in Norway?", "en"),
        ("Hva er gjennomsnittlig matbudsjett i Norge?", "no"),
        ("Transport costs", "en"),
        ("Transportkostnader", "no"),
    ]
    
    print("🧪 Testing Language Detection:\n")
    for text, expected in test_cases:
        detected = detector.detect(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{text[:50]}...' → {detected} (expected: {expected})")


if __name__ == "__main__":
    test_language_detection()