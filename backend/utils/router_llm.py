import openai
from mistralai import Mistral
from config import Config
import logging

logger = logging.getLogger(__name__)

class RouterLLM:
    def __init__(self, provider: str = "openai"):
        self.provider = provider.lower()
        self.api_key = None
        self.client = None

        if self.provider == "openai":
            self.api_key = Config.LLM_API_KEY
            if not self.api_key:
                raise ValueError("A chave de API do OpenAI não foi fornecida.")
            openai.api_key = self.api_key
            self.client = openai
        elif self.provider == "mistral":
            self.api_key = Config.MISTRAL_API_KEY
            if not self.api_key:
                raise ValueError("A chave de API do Mistral não foi fornecida.")
            self.client = Mistral(api_key=self.api_key)
        elif self.provider == "local":
            self.client = None
        else:
            raise ValueError(f"Provedor LLM desconhecido: {self.provider}")

    def validate_api_key(self) -> bool:
        """Valida se a chave de API foi configurada corretamente."""
        try:
            if self.provider == "openai":
                self.client.Model.list()
                return True
            elif self.provider == "mistral":
                # Test Mistral API with a simple chat request
                self.client.chat(
                    model="mistral-tiny",
                    messages=[{"role": "user", "content": "test"}]
                )
                return True
            elif self.provider == "local":
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao validar chave de API para {self.provider}: {str(e)}")
            return False

    def process_text(self, input_data: str, model: str = None) -> str:
        """Processa o texto usando o provedor configurado."""
        try:
            if self.provider == "openai":
                response = self.client.ChatCompletion.create(
                    model=model or Config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a medical data analysis assistant."},
                        {"role": "user", "content": input_data}
                    ]
                )
                return response.choices[0].message.content
            elif self.provider == "mistral":
                response = self.client.chat(
                    model=model or "mistral-tiny",
                    messages=[
                        {"role": "system", "content": "You are a medical data analysis assistant."},
                        {"role": "user", "content": input_data}
                    ]
                )
                return response.choices[0].message.content
            elif self.provider == "local":
                return f"Resultado processado localmente: {input_data}"
        except Exception as e:
            logger.error(f"Erro ao processar texto com {self.provider}: {str(e)}")
            # Tentar fallback para processamento local
            if self.provider != "local":
                logger.info("Tentando fallback para processamento local")
                self.provider = "local"
                return self.process_text(input_data)
            raise Exception(f"Erro ao processar texto com {self.provider}: {str(e)}")