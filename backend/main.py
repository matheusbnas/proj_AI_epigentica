import os
import logging
from fastapi import FastAPI, UploadFile, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from extrator_dados_tecnicos import ExtratorDadosTecnicos
from dotenv import load_dotenv, find_dotenv

# Add these imports at the top
from google_slides_client import GoogleSlidesClient
from config import Config
from utils.data_processor import DataProcessor

# Initialize new components
from utils.router_llm import LLMRouter
from utils.slides_processor import SlidesProcessor

# Load environment variables 
_ = load_dotenv(find_dotenv())

app = FastAPI()

# Configuração avançada de logs
def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Handler para arquivo
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Handler para console 
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logging()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Modify WebSocket connections to include process_id
connected_clients = {}

@app.websocket("/ws/{process_id}")
async def websocket_endpoint(websocket: WebSocket, process_id: str):
    await websocket.accept()
    connected_clients[process_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        if process_id in connected_clients:
            del connected_clients[process_id]

async def notify_client(process_id: str, message: dict):
    """Notify specific WebSocket client"""
    if process_id in connected_clients:
        try:
            await connected_clients[process_id].send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")

# Inicializar Google Slides Client
slides_client = GoogleSlidesClient(
    credentials_path=".credentials/credentials.json",
)

# Initialize components
llm_router = LLMRouter()  # Remove api_key parameter since it will use environment variable
slides_processor = SlidesProcessor(llm_router)

@app.post("/process-pdf")
async def process_pdf(file: UploadFile):
    """Process uploaded PDF file and extract data"""
    process_id = datetime.now().strftime("%Y%m%d%H%M%S")  # Generate unique process_id
    logger.info(f"Starting new process with ID: {process_id}")
    logger.debug(f"Arquivo recebido: {file.filename}")
    
    # Setup directories
    output_dir = "output"
    figs_dir = "figs"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(figs_dir, exist_ok=True)

    # Generate output filename with date
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = f"extracted_text_result.json"
    output_path = os.path.join(output_dir, output_file)

    try:
        # Check if JSON already exists
        json_path = os.path.join(output_dir, "dados.json")
        if os.path.exists(json_path):
            logger.info(f"[{process_id}] Found existing JSON data, skipping PDF processing")
            logger.debug(f"[{process_id}] Carregando dados do arquivo: {json_path}")
            with open(json_path, "r", encoding="utf-8") as f:
                result = json.load(f)
            
            logger.info(f"[{process_id}] Transforming existing JSON to slides format")
            initial_slides = DataProcessor.transform_to_slides(result)
            
            await notify_client(process_id, {
                "type": "progress",
                "progress": 60,
                "message": "Dados JSON encontrados, gerando slides...",
                "slides": initial_slides
            })
        else:
            logger.info(f"[{process_id}] Processing new PDF file: {file.filename}")
            
            # Validate file type
            if not file.filename.endswith('.pdf'):
                raise HTTPException(400, "Only PDF files are accepted")

            # Save uploaded PDF
            temp_pdf = os.path.join(output_dir, file.filename)
            content = await file.read()
            with open(temp_pdf, "wb") as pdf_file:
                pdf_file.write(content)

            logger.info(f"PDF saved to: {temp_pdf}")
            
            # Initial progress update
            await notify_client(process_id, {
                "type": "progress",
                "progress": 5,
                "message": "Iniciando OCR..."
            })
            
            logger.info(f"[{process_id}] Starting OCR processing")
            # Process PDF with Mistral OCR
            extractor = ExtratorDadosTecnicos(
                api_key=os.getenv("MISTRAL_API_KEY"),
                output_dir=output_dir,
                figs_dir=figs_dir
            )
            
            # Process in chunks and update progress
            result = extractor.processar_arquivo(temp_pdf)
            logger.info(f"[{process_id}] OCR processing completed")
            
            # Update progress after extraction
            await notify_client(process_id, {
                "type": "progress",
                "progress": 30,
                "message": "Dados extraídos, processando..."
            })

            if not result:
                logger.error(f"[{process_id}] Failed to extract data from PDF")
                raise HTTPException(500, "Failed to extract data from PDF")

            logger.info(f"[{process_id}] Data extracted successfully")
            logger.debug(f"[{process_id}] Extracted data structure: {list(result.keys())}")

            # Process initial slides data
            initial_slides = DataProcessor.transform_to_slides(result)
            
            # Send initial slides to client
            await notify_client(process_id, {
                "type": "progress",
                "progress": 60,
                "message": "Gerando slides iniciais...",
                "slides": initial_slides
            })

        # Process enhanced slides with LLM
        async def progress_callback(progress, message):
            actual_progress = 60 + int(progress * 0.4)  # Scale progress from 60-100%
            await notify_client(process_id, {
                "type": "progress",
                "progress": actual_progress,
                "message": message
            })

        logger.info(f"[{process_id}] Starting LLM processing")
        final_slides = await slides_processor.process_report_data(
            result, 
            progress_callback=progress_callback
        )
        logger.info(f"[{process_id}] LLM processing completed")
        
        # Save processed slides
        slides_json_path = os.path.join(output_dir, "slides_data.json")
        logger.info(f"[{process_id}] Saving final slides to {slides_json_path}")
        with open(slides_json_path, "w", encoding="utf-8") as f:
            json.dump(final_slides, f, ensure_ascii=False, indent=2)
        
        await notify_client(process_id, {
            "type": "complete",
            "progress": 100,
            "slides": final_slides
        })

        return {
            "process_id": process_id,
            "slides": final_slides
        }

    except HTTPException as e:
        logger.error(f"HTTP Error: {e.detail}")
        await notify_client(process_id, {
            "type": "error",
            "process_id": process_id,
            "message": str(e)
        })
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        await notify_client(process_id, {
            "type": "error",
            "process_id": process_id,
            "message": str(e)
        })
        raise HTTPException(500, f"Processing error: {str(e)}")

@app.post("/create-google-slides")
async def create_google_slides(process_id: str):
    logger.info(f"[{process_id}] Starting Google Slides creation")
    try:
        # Load processed slides data
        slides_json_path = os.path.join("output", "slides_data.json")
        if not os.path.exists(slides_json_path):
            logger.error(f"[{process_id}] Slides data not found at {slides_json_path}")
            raise HTTPException(404, "Processed slides data not found")
            
        await notify_client(process_id, {
            "type": "progress",
            "progress": 80,
            "message": "Criando apresentação no Google Slides..."
        })
        
        logger.info(f"[{process_id}] Creating Google Slides presentation")
        # Create Google Slides presentation
        presentation_url = slides_client.create_slides_from_json(slides_json_path)
        logger.info(f"[{process_id}] Presentation created successfully: {presentation_url}")
        
        await notify_client(process_id, {
            "type": "complete",
            "progress": 100,
            "message": "Apresentação criada com sucesso!",
            "presentation_url": presentation_url
        })
        
        return {"presentation_url": presentation_url}
        
    except Exception as e:
        logger.error(f"[{process_id}] Error creating Google Slides: {str(e)}", exc_info=True)
        await notify_client(process_id, {
            "type": "error",
            "message": f"Error creating presentation: {str(e)}"
        })
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)