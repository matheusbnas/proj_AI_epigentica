import os
import logging
from fastapi import FastAPI, UploadFile, HTTPException, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from contextlib import asynccontextmanager
from extrator_dados_tecnicos import ExtratorDadosTecnicos
from google_slides_client import GoogleSlidesClient
from dotenv import load_dotenv, find_dotenv
import asyncio
from typing import Dict
from starlette.websockets import WebSocketDisconnect

# Load environment variables
_ = load_dotenv(find_dotenv())

# Setup startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    # Initialize services
    slides_client = GoogleSlidesClient(
        credentials_path=".credentials/credentials.json",
        template_presentation_id=os.getenv("TEMPLATE_PRESENTATION_ID")  # Corrigido para usar o ID do template
    )
    app.state.slides_client = slides_client
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    # Cleanup WebSocket connections
    for ws in connected_clients.values():
        await ws.close()
    connected_clients.clear()

app = FastAPI(lifespan=lifespan)

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

# Add process tracking with timeouts
active_processes: Dict[str, dict] = {}
PROCESS_TIMEOUT = 600  # 10 minutes timeout

async def handle_websocket_connection(websocket: WebSocket, process_id: str):
    """Handle WebSocket connection with proper error handling"""
    try:
        await websocket.accept()
        connected_clients[process_id] = websocket
        
        ping_interval = 30  # seconds
        ping_timeout = 10   # seconds
        
        while True:
            try:
                # Wait for message or timeout
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=ping_interval
                )
                
                if message == "pong":
                    continue
                    
            except asyncio.TimeoutError:
                # Send ping
                try:
                    await websocket.send_text("ping")
                    # Wait for pong
                    await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=ping_timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"WebSocket ping timeout for process {process_id}")
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for process {process_id}")
    except Exception as e:
        logger.error(f"WebSocket error for process {process_id}: {str(e)}")
    finally:
        if process_id in connected_clients:
            del connected_clients[process_id]

@app.websocket("/ws/{process_id}")
async def websocket_endpoint(websocket: WebSocket, process_id: str):
    await handle_websocket_connection(websocket, process_id)

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
    template_presentation_id=os.getenv("TEMPLATE_PRESENTATION_ID")  # Corrigido para usar o ID do template
)

class DataProcessor:
    @staticmethod
    def transform_to_slides(data):
        sections = []
        for item in data:
            if isinstance(item, dict):
                section = {
                    "type": "section",
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "images": item.get("images", [])
                }
                sections.append(section)
        return sections

# Add process tracking
active_processes: Dict[str, dict] = {}

async def handle_progress_update(process_id: str, stage: str, progress: int):
    """Handle progress updates from the extractor"""
    if process_id in active_processes:
        try:
            await notify_client(process_id, {
                "type": "progress",
                "stage": stage,
                "progress": progress,
                "message": f"Processando... {progress}%"
            })
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")

async def process_pdf_background(process_id: str, file_path: str):
    try:
        active_processes[process_id] = {"status": "processing", "progress": 0}
        
        # Define sync progress callback
        def progress_callback(stage: str, progress: int):
            # Use asyncio.create_task to handle the async notification
            asyncio.create_task(notify_client(process_id, {
                "type": "progress",
                "stage": stage,
                "progress": progress,
                "message": f"Processando... {progress}%"
            }))

        # Initialize extractor with sync callback
        extractor = ExtratorDadosTecnicos(
            api_key=os.getenv("MISTRAL_API_KEY"),
            output_dir="output",
            figs_dir="figs",
            progress_callback=progress_callback
        )

        # Initialize progress
        active_processes[process_id] = {"status": "processing", "progress": 0}
        
        # Update client about OCR start
        await notify_client(process_id, {
            "type": "status",
            "stage": "PROCESSING_PDF",
            "progress": 10,
            "message": "Iniciando processamento do PDF..."
        })

        # Create progress callback that works with async
        async def progress_callback(stage: str, progress: int):
            await handle_progress_update(process_id, stage, progress)

        # Initialize extractor with progress callback
        extractor = ExtratorDadosTecnicos(
            api_key=os.getenv("MISTRAL_API_KEY"),
            output_dir="output",
            figs_dir="figs",
            progress_callback=lambda stage, progress: asyncio.run(progress_callback(stage, progress))
        )
        
        # Process PDF in chunks
        result = await asyncio.get_event_loop().run_in_executor(
            None, extractor.processar_arquivo, file_path
        )

        if not result:
            raise Exception("Falha ao extrair dados do PDF")

        # Process slides data
        await notify_client(process_id, {
            "type": "status",
            "stage": "CREATING_SLIDES",
            "progress": 70,
            "message": "Gerando apresentação..."
        })

        # Create Google Slides presentation
        presentation_result = await create_google_presentation(process_id, result)
        
        # Send final success response
        await notify_client(process_id, {
            "type": "complete",
            "slides": result,
            "presentation_url": presentation_result.get("presentation_url"),
            "slide_id": presentation_result.get("slide_id")
        })

    except Exception as e:
        logger.error(f"Error in background process: {str(e)}")
        await notify_client(process_id, {
            "type": "error",
            "message": str(e)
        })
    finally:
        if process_id in active_processes:
            del active_processes[process_id]

async def create_google_presentation(process_id: str, slides_data: list):
    try:
        await notify_client(process_id, {
            "type": "status",
            "stage": "CREATING_PRESENTATION",
            "progress": 80,
            "message": "Criando apresentação no Google Slides..."
        })
        
        # Certifique-se de que slides_data é um objeto/lista e não uma string
        if isinstance(slides_data, str):
            try:
                slides_data = json.loads(slides_data)
            except json.JSONDecodeError:
                raise Exception("Formato de dados inválido para criação de slides")
        
        # Transformar dados para o formato esperado pelo Google Slides
        processed_slides = DataProcessor.transform_to_slides(slides_data)
        
        presentation_id = slides_client.create_slides_from_json(processed_slides)
        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        first_slide = slides_client.get_first_slide_id(presentation_id)
        
        return {
            "presentation_url": presentation_url,
            "slide_id": first_slide
        }
    except Exception as e:
        logger.error(f"Error creating presentation: {str(e)}")
        raise

@app.post("/process-pdf")
async def process_pdf(file: UploadFile, background_tasks: BackgroundTasks):
    """Process uploaded PDF file and extract data"""
    process_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    try:
        # Save uploaded file
        file_path = os.path.join("output", file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Start background processing and cleanup
        background_tasks.add_task(process_pdf_background, process_id, file_path)
        background_tasks.add_task(cleanup_process, process_id)
        
        return {"process_id": process_id, "status": "processing"}
        
    except Exception as e:
        logger.error(f"Error initiating process: {str(e)}")
        raise HTTPException(500, str(e))

async def cleanup_process(process_id: str):
    """Cleanup process after timeout"""
    await asyncio.sleep(PROCESS_TIMEOUT)
    if process_id in active_processes:
        logger.warning(f"Process {process_id} timed out")
        await notify_client(process_id, {
            "type": "error",
            "message": "Processo expirou por timeout"
        })
        del active_processes[process_id]

@app.post("/create-google-slides")
async def create_google_slides(process_id: str):
    slides_client = app.state.slides_client
    logger.info(f"[{process_id}] Starting Google Slides creation")
    try:
        # Load and parse JSON file
        slides_json_path = os.path.join("output", "slides_data.json")
        if not os.path.exists(slides_json_path):
            logger.error(f"[{process_id}] Slides data not found at {slides_json_path}")
            raise HTTPException(404, "Processed slides data not found")
        
        # Carregar JSON como objeto, não como string
        with open(slides_json_path, 'r', encoding='utf-8') as f:
            slides_data = json.load(f)
        
        await notify_client(process_id, {
            "type": "progress",
            "progress": 80,
            "message": "Criando apresentação no Google Slides..."
        })
        
        logger.info(f"[{process_id}] Creating Google Slides presentation")
        # Create Google Slides presentation
        presentation_id = slides_client.create_slides_from_json(slides_data)
        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        
        # Get first slide ID
        first_slide = slides_client.get_first_slide_id(presentation_id)
        
        await notify_client(process_id, {
            "type": "complete",
            "progress": 100,
            "message": "Apresentação criada com sucesso!",
            "presentation_url": presentation_url,
            "slide_id": first_slide
        })
        
        return {
            "presentation_url": presentation_url,
            "slide_id": first_slide
        }
        
    except Exception as e:
        logger.error(f"Error creating Google Slides: {str(e)}", exc_info=True)
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    config = uvicorn.Config("main:app", 
                           host="0.0.0.0", 
                           port=8000,
                           reload=True,
                           reload_delay=1,
                           log_level="info")
    server = uvicorn.Server(config)
    server.run()