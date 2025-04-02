# utils/llm_handler.py
from utils.router_llm import RouterLLM
from config import Config

class LLMHandler:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.router = RouterLLM(provider=provider)
        if not self.router.validate_api_key():
            raise ValueError(f"A chave de API para o provedor {provider} é inválida ou não pode ser validada.")

    def extract_medical_data(self, input_data: str) -> str:
        """Extrai dados médicos usando o provedor configurado."""
        try:
            return self.router.process_text(input_data)
        except Exception as e:
            # Fallback para outro provedor em caso de erro
            fallback_provider = "mistral" if self.provider == "openai" else "local"
            self.router = RouterLLM(provider=fallback_provider)
            return self.router.process_text(input_data)