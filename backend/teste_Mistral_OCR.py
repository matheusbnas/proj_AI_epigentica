# Exemplo completo de uso
from mistralai import Mistral, DocumentURLChunk
import json
import time
import logging

# Configurar logging para depuração
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = Mistral(api_key="8RAlcHdIBJxaHwa93j679JUNPaPkbpw2")

# Upload do arquivo
uploaded_file = client.files.upload(
    file={
        "file_name": "../data/dados.pdf",
        "content": open("../data/dados.pdf", "rb")
    },
    purpose="ocr"
)

# Obter URL assinada para o arquivo enviado
signed_url = client.files.get_signed_url(
    file_id=uploaded_file.id,
    expiry=1  # Tempo de expiração em horas
)

# Processar OCR para extrair texto
ocr_result = client.ocr.process(
    model="mistral-ocr-latest",
    document=DocumentURLChunk(document_url=signed_url.url)
)

# Converter o resultado para um dicionário antes de salvar
ocr_result_dict = ocr_result.model_dump()  # Substituído .dict() por .model_dump()

# Salvando o resultado em um arquivo JSON
with open("extracted_text_result.json", "w") as output_file:
    json.dump(ocr_result_dict, output_file, indent=4)
    time.sleep(1)  # Aguardar 1 segundo para garantir que o arquivo seja salvo corretamente

# Carregar os dados extraídos
with open("extracted_text_result.json", "r") as input_file:
    extracted_data = json.load(input_file)

# Verificar se o texto foi extraído
extracted_text = extracted_data.get("text", "")
if not extracted_text.strip():
    print("Nenhum texto foi extraído do documento. Verifique o arquivo PDF ou o processo de OCR.")
    logger.error(f"Dados extraídos: {extracted_data}")  # Log para depuração
else:
    # Formatar o texto extraído
    formatted_text = f"""
    ============================
    TEXTO EXTRAÍDO DO DOCUMENTO
    ============================
    {extracted_text.strip()}
    ============================
    """
    print(formatted_text)

    # Criar um arquivo .txt com os dados extraídos
    with open("extracted_text_result.txt", "w", encoding="utf-8") as txt_file:
        txt_file.write("TEXTO EXTRAÍDO DO DOCUMENTO\n")
        txt_file.write("=" * 30 + "\n")
        txt_file.write(extracted_text.strip() + "\n")
        txt_file.write("=" * 30 + "\n")

    print("Os dados extraídos foram salvos no arquivo 'extracted_text_result.txt'.")