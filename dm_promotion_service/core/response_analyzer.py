import logging
import yaml
from pathlib import Path
from Free_API_Load_balancer import generate


class ResponseAnalyzer:
    """Analyze user messages and responses using AI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        config_path = Path(__file__).parent.parent / "config" / "level_messages.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    async def categorize_user(self, message: str) -> bool:
        """Categorize if user is looking for jobs (True) or not (False)"""
        try:
            prompt = self.config['categorization_prompt'].format(message=message)
            
            response = generate(prompt=prompt, max_output_tokens=10)
            response = response.strip().lower()
            
            return "yes" in response
            
        except Exception as e:
            self.logger.error(f"Error categorizing user message: {e}")
            return False
    
    def analyze_response(self, response_text: str, level: str = None) -> str:
        """Analyze response: returns 'yes', 'no', or 'unclear'. Uses per-level prompts when available."""
        try:
            if not response_text:
                return "unclear"

            # Choose prompt: per-level prompt if available, otherwise generic
            prompt_template = None
            if level:
                prompt_template = self.config.get('response_prompts', {}).get(level)

            if prompt_template:
                prompt = prompt_template.format(message=response_text.strip())
            else:
                prompt = (
                    "You are a classifier. Determine if the user's reply to a job offer is an affirmative 'yes', "
                    "a negative 'no', or 'unclear'. Reply with only one word: yes, no, or unclear.\n\n"
                    "User reply: \"" + response_text.strip() + "\""
                )

            try:
                ai_response = generate(prompt=prompt, max_output_tokens=10)
                ai_response = ai_response.strip().lower()

                if ai_response.startswith("yes") or "yes" in ai_response:
                    return "yes"
                if ai_response.startswith("no") or "no" in ai_response:
                    return "no"
                return "unclear"
            except Exception as e:
                # Fallback to lightweight keyword matching if AI call fails
                self.logger.warning(f"AI analyze_response failed, falling back to keywords: {e}")

                text = response_text.strip().lower()
                yes_keywords = ['yes', 'yeah', 'yep', 'yup', 'ok', 'okay', 'sure', 'pls', 'please', 'fine', 'alright']
                no_keywords = ['no', 'nope', 'nah', "can't", 'cannot', 'not interested', 'busy']

                for keyword in yes_keywords:
                    if keyword in text:
                        return "yes"
                for keyword in no_keywords:
                    if keyword in text:
                        return "no"
                return "unclear"

        except Exception as e:
            self.logger.error(f"Error analyzing response: {e}")
            return "unclear"
