import json
import os
import logging
from typing import Dict, Any, List, Optional
from mistralai import Mistral, DocumentURLChunk, ImageURLChunk, TextChunk
from mistralai.models.sdkerror import SDKError
import re

logger = logging.getLogger(__name__)

# Classe Document personalizada
class Document:
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}

class PDFProcessor:
    def __init__(self, file_path: str, mistral_api_key: str):
        if not mistral_api_key:
            raise ValueError("A chave de API Mistral não foi fornecida.")
        self.file_path = file_path
        self.client = Mistral(api_key=mistral_api_key)

    def _call_mistral_ocr(self) -> str:
        """Processa o PDF usando OCR e salva o resultado em JSON."""
        try:
            # Upload do arquivo para a API
            logger.info(f"Fazendo upload do arquivo: {self.file_path}")
            with open(self.file_path, "rb") as file_content:
                uploaded_file = self.client.files.upload(
                    file={
                        "file_name": os.path.basename(self.file_path),
                        "content": file_content,
                    },
                    purpose="ocr"
                )

            # Obter URL assinada para o arquivo enviado
            logger.info("Obtendo URL assinada para o arquivo enviado.")
            signed_url = self.client.files.get_signed_url(
                file_id=uploaded_file.id,
                expiry=1  # Tempo de expiração em horas
            )

            # Processar OCR para extrair texto
            logger.info("Processando OCR para extrair texto.")
            ocr_result = self.client.ocr.process(
                model="mistral-ocr-latest",
                document=DocumentURLChunk(document_url=signed_url.url)
            )

            # Converter o resultado para um dicionário e salvar em JSON
            ocr_result_dict = ocr_result.model_dump()
            output_path = os.path.join("output", "extracted_text_result.json")
            os.makedirs("output", exist_ok=True)  # Garantir que a pasta de saída exista
            with open(output_path, "w", encoding="utf-8") as output_file:
                json.dump(ocr_result_dict, output_file, indent=4)

            logger.info(f"OCR concluído. Resultado salvo em: {output_path}")
            return output_path

        except SDKError as e:
            if e.status_code == 401:
                logger.error("Erro de autenticação: Verifique sua chave de API Mistral.")
                raise Exception("Erro de autenticação: Verifique sua chave de API Mistral.")
            logger.error(f"Erro na API Mistral: {e}")
            raise Exception(f"Erro na API Mistral: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado no OCR: {e}")
            raise Exception(f"Erro inesperado no OCR: {e}")

    def extract_data(self) -> dict:
        """Extrai dados do JSON gerado pelo OCR."""
        try:
            logger.info("Iniciando extração de dados do PDF.")
            json_path = self._call_mistral_ocr()
            with open(json_path, "r", encoding="utf-8") as json_file:
                extracted_data = json.load(json_file)
            logger.debug(f"Dados extraídos: {extracted_data}")
            return extracted_data
        except Exception as e:
            logger.error(f"Erro crítico durante a extração de dados: {e}")
            return {"error": str(e), "source": "OCR"}

    def validate_pdf(file_path: str):
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                if header != b"%PDF":
                    raise ValueError("Invalid PDF header")
        except Exception as e:
            logger.error(f"Invalid PDF: {str(e)}")
            raise

    # Métodos de extração mantidos originais
    def _extract_patient_info(self, text: str) -> Dict[str, str]:
        return {
            "name": re.search(r"Paciente:\s*(.*)", text).group(1).strip() if re.search(r"Paciente:", text) else "N/A",
            "age": re.search(r"Idade:\s*(\d+)", text).group(1) if re.search(r"Idade:", text) else "N/A",
            "code": re.search(r"Código:\s*(\w+)", text).group(1) if re.search(r"Código:", text) else "N/A"
        }

    def _extract_genetic_data(self, text: str) -> list:
        sections = re.split(r"\n={5,}\s*Page \d+ =====\n", text)
        genetic_data = []

        for section in sections:
            if "RESULTADO GENÉTICO DETALHADO" in section:
                category_match = re.search(r"# (.+?)\n", section)
                category = category_match.group(1).strip() if category_match else "Geral"

                genes = re.findall(
                    r"\|(.+?)\|(.+?)\|(.+?)\|(.+?)\|(.+?)\|",
                    section,
                    re.DOTALL
                )

                table_data = [{
                    "funcao": g[0].strip(),
                    "gene": g[1].strip(),
                    "dbSNP": g[2].strip(),
                    "risco": g[3].strip(),
                    "resultado": g[4].strip()
                } for g in genes if len(g) >= 5]

                comments_match = re.search(r"COMENTÁRIOS\s*\n(.+?)(?=\n\s*\n)", section, re.DOTALL)
                comments = comments_match.group(1).strip() if comments_match else ""

                genetic_data.append({
                    "category": category,
                    "genes": table_data,
                    "comments": comments
                })

        return genetic_data

    def _extract_recommendations(self, text: str) -> list:
        nutrition_block = re.search(
            r"RECOMENDAÇÕES NUTRICIONAIS(.+?)(?=\n#{2,}|$)",
            text,
            re.DOTALL
        )
        if nutrition_block:
            return [rec.strip() for rec in re.split(r"\n\s*•\s*", nutrition_block.group(1)) if rec.strip()]
        return []