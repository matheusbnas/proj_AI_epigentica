import os
import logging
from fastapi import FastAPI, UploadFile, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import websockets
import asyncio
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pdf_processor import PDFProcessor
from google_slides_client import GoogleSlidesClient
import tempfile
from dotenv import load_dotenv, find_dotenv
import uuid
from utils.llm_handler import LLMHandler
from datetime import datetime

# Load environment variables
_ = load_dotenv(find_dotenv())

app = FastAPI()

# Configurações
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS_JSON")
TEMPLATE_ID = os.getenv("TEMPLATE_PRESENTATION_ID")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# WebSocket
connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Mantém a conexão ativa
    except Exception as e:
        logger.error(f"Erro WebSocket: {str(e)}")
    finally:
        connected_clients.remove(websocket)

async def notify_clients(message: dict):
    """Notifica todos os clientes conectados via WebSocket."""
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem WebSocket: {str(e)}")

@app.post("/process-pdf")
async def process_pdf(file: UploadFile, llm_provider: str = "openai"):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    output_file_name = f"{os.path.splitext(file.filename)[0]}_{today}.pdf"
    output_path = os.path.join(output_dir, output_file_name)

    process_id = str(uuid.uuid4())

    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "Apenas arquivos PDF são aceitos.")

        # Salvar o arquivo PDF
        with open(output_path, "wb") as output_file:
            content = await file.read()
            output_file.write(content)

        logger.info(f"Arquivo PDF salvo em: {output_path}")
        await notify_clients({"type": "status", "process_id": process_id, "message": "Processamento iniciado"})

        # Processar o PDF com OCR
        processor = PDFProcessor(file_path=output_path, mistral_api_key=os.getenv("MISTRAL_API_KEY"))
        extracted_data = processor.extract_data()

        if "error" in extracted_data:
            logger.error(f"Erro ao extrair dados do PDF: {extracted_data['error']}")
            raise HTTPException(500, extracted_data["error"])

        logger.info("Dados extraídos do PDF com sucesso.")

        # Processar os dados extraídos com LLM
        llm_handler = LLMHandler(provider=llm_provider)
        analysis_result = llm_handler.extract_medical_data(json.dumps(extracted_data))

        # Salvar o resultado da análise
        analysis_file_name = f"analysis_result_{process_id}.json"
        analysis_path = os.path.join(output_dir, analysis_file_name)
        with open(analysis_path, "w", encoding="utf-8") as analysis_file:
            analysis_file.write(analysis_result)

        logger.info(f"Análise concluída e salva em: {analysis_path}")

        # Notificar clientes WebSocket sobre a conclusão
        await notify_clients({
            "type": "complete",
            "process_id": process_id,
            "slides": json.loads(analysis_result)
        })

        return {"process_id": process_id, "output_path": output_path, "analysis_path": analysis_path}

    except HTTPException as e:
        logger.error(f"Erro HTTP: {e.detail}")
        await notify_clients({"type": "error", "process_id": process_id, "message": e.detail})
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        await notify_clients({"type": "error", "process_id": process_id, "message": str(e)})
        raise HTTPException(500, f"Erro no processamento: {str(e)}")

@app.post("/create-slides")
async def create_slides():
    try:
        # Caminho do arquivo JSON
        json_path = "output/extracted_text_result.json"

        # Inicializa o cliente do Google Slides
        google_slides_client = GoogleSlidesClient(
            credentials_path=os.getenv("GOOGLE_CREDENTIALS_JSON"),
            template_presentation_id=os.getenv("TEMPLATE_PRESENTATION_ID")
        )

        # Cria os slides e retorna o link
        presentation_url = google_slides_client.create_slides_from_json(json_path)
        return {"presentation_url": presentation_url}

    except Exception as e:
        raise HTTPException(500, f"Erro ao criar slides: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)