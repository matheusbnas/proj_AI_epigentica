import logging
from config import Config
from mistralai import MistralClient

logger = logging.getLogger(__name__)

class LLMRouter:
    def __init__(self):
        try:
            self.mistral_client = MistralClient(api_key=Config.MISTRAL_API_KEY)
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")
            raise

    async def process_text(self, text: str, context: str = "") -> str:
        try:
            response = self.mistral_client.chat(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em resumir e estruturar texto para apresentações."},
                    {"role": "user", "content": f"Contexto: {context}\n\nTexto: {text}\n\nResuma este texto em formato adequado para slides."}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
