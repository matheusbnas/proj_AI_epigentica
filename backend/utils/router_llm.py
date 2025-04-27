import openai
from mistralai import Mistral
import logging
from enum import Enum

# Optional import for Anthropic
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not installed. Claude models will not be available.")

from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    OPENAI = "openai"
    MISTRAL = "mistral"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

class ModelConfig:
    def __init__(self, 
                 name: str, 
                 provider: ModelProvider,
                 cost_per_1k_input: float,
                 cost_per_1k_output: float,
                 max_tokens: int,
                 quality_score: float):
        self.name = name
        self.provider = provider
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self.max_tokens = max_tokens
        self.quality_score = quality_score

class LLMRouter:  # Changed from RouterLLM to LLMRouter
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LLMRouter with optional API key"""
        self.models = {
            # OpenAI Models
            "gpt-4": ModelConfig("gpt-4", ModelProvider.OPENAI, 0.03, 0.06, 8192, 0.95),
            "gpt-3.5-turbo": ModelConfig("gpt-3.5-turbo", ModelProvider.OPENAI, 0.0015, 0.002, 4096, 0.85),
            
            # Mistral Models
            "mistral-large": ModelConfig("mistral-large", ModelProvider.MISTRAL, 0.02, 0.06, 4096, 0.90),
            "mistral-medium": ModelConfig("mistral-medium", ModelProvider.MISTRAL, 0.007, 0.02, 4096, 0.85),
            
            # Anthropic Models
            "claude-2": ModelConfig("claude-2", ModelProvider.ANTHROPIC, 0.03, 0.08, 100000, 0.95),
            "claude-instant": ModelConfig("claude-instant", ModelProvider.ANTHROPIC, 0.0015, 0.003, 100000, 0.82),
        }
        
        self.clients = {}
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize API clients for each provider"""
        try:
            if Config.OPENAI_API_KEY:
                self.clients[ModelProvider.OPENAI] = openai.Client(api_key=Config.OPENAI_API_KEY)
            if Config.MISTRAL_API_KEY:
                self.clients[ModelProvider.MISTRAL] = Mistral(api_key=Config.MISTRAL_API_KEY)
            if ANTHROPIC_AVAILABLE and Config.ANTHROPIC_API_KEY:
                self.clients[ModelProvider.ANTHROPIC] = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")

    def select_model(self, 
                    input_length: int,
                    min_quality: float = 0.8,
                    max_cost: float = float('inf')) -> Optional[str]:
        """Select best model based on input length, quality requirements and cost constraints"""
        best_model = None
        best_score = float('-inf')
        
        for model_name, config in self.models.items():
            # Skip if provider client not initialized
            if config.provider not in self.clients:
                continue
                
            # Check constraints
            if config.quality_score < min_quality:
                continue
            
            estimated_cost = ((input_length * config.cost_per_1k_input) + 
                            (input_length * 0.5 * config.cost_per_1k_output)) / 1000
            
            if estimated_cost > max_cost:
                continue
                
            # Calculate score (quality/cost ratio)
            score = config.quality_score / estimated_cost
            
            if score > best_score:
                best_score = score
                best_model = model_name
        
        return best_model

    async def process_text(self, 
                         input_data: str,
                         min_quality: float = 0.8,
                         max_cost: float = float('inf')) -> str:
        """Process text using the best available model"""
        try:
            input_length = len(input_data.split())
            model_name = self.select_model(input_length, min_quality, max_cost)
            
            if not model_name:
                raise Exception("No suitable model found for given constraints")
                
            model_config = self.models[model_name]
            client = self.clients[model_config.provider]
            
            if model_config.provider == ModelProvider.OPENAI:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a medical data analysis assistant."},
                        {"role": "user", "content": input_data}
                    ]
                )
                return response.choices[0].message.content
                
            elif model_config.provider == ModelProvider.MISTRAL:
                response = await client.chat(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a medical data analysis assistant."},
                        {"role": "user", "content": input_data}
                    ]
                )
                return response.choices[0].message.content
                
            elif model_config.provider == ModelProvider.ANTHROPIC:
                response = await client.messages.create(
                    model=model_name,
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": input_data}
                    ]
                )
                return response.content[0].text
                
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            # Fallback to local processing if everything fails
            return f"Local fallback processing: {input_data}"

router = LLMRouter()

async def process_medical_report():
    result = await router.process_text(
        input_data="Analyze this medical report...",
        min_quality=0.85,  # Minimum quality score
        max_cost=0.10     # Maximum cost in USD
    )
    return result
