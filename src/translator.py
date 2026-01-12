"""
MWhisper Translator
Translates text using OpenAI GPT API
"""

from typing import Optional


class Translator:
    """Handles text translation via OpenAI API"""
    
    DEFAULT_PROMPT = (
        "Переведи этот текст на английский язык. "
        "Исправь ошибки и напиши простыми словами. "
        "Верни ТОЛЬКО перевод, без пояснений."
    )
    
    def __init__(self, api_key: str, prompt: Optional[str] = None):
        """
        Initialize translator.
        
        Args:
            api_key: OpenAI API key
            prompt: Custom translation prompt (optional)
        """
        self.api_key = api_key
        self.prompt = prompt or self.DEFAULT_PROMPT
        self._client = None
    
    def _ensure_client(self):
        """Lazy load OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("Error: openai package not installed. Run: pip install openai")
                raise
        return self._client
    
    def translate(self, text: str, target_language: str = "English") -> Optional[str]:
        """
        Translate text using OpenAI GPT.
        
        Args:
            text: Text to translate
            target_language: Target language (default: English)
        
        Returns:
            Translated text or None if failed
        """
        if not text or not text.strip():
            return None
        
        if not self.api_key:
            print("Error: OpenAI API key not configured")
            return None
        
        try:
            client = self._ensure_client()
            
            # Build the prompt with target language
            system_prompt = self.prompt.replace("английский", target_language.lower())
            
            print(f"🌐 Sending to OpenAI for translation...")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=1000,
                temperature=0.3  # Low temperature for consistent translations
            )
            
            translated = response.choices[0].message.content.strip()
            print(f"✓ Translation received: {translated[:50]}...")
            
            return translated
            
        except Exception as e:
            print(f"Translation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_connection(self) -> bool:
        """
        Test if API key is valid.
        
        Returns:
            True if connection successful
        """
        try:
            client = self._ensure_client()
            # Simple test - list models
            client.models.list()
            return True
        except Exception as e:
            print(f"API connection test failed: {e}")
            return False


def translate_text(text: str, api_key: str, prompt: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to translate text.
    
    Args:
        text: Text to translate
        api_key: OpenAI API key
        prompt: Custom prompt (optional)
    
    Returns:
        Translated text or None
    """
    translator = Translator(api_key, prompt)
    return translator.translate(text)


# Test
if __name__ == "__main__":
    import os
    
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("Set OPENAI_API_KEY environment variable to test")
    else:
        translator = Translator(api_key)
        if translator.test_connection():
            print("✓ Connection OK")
            result = translator.translate("Привет, как дела?")
            print(f"Result: {result}")
