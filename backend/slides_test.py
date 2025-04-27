import sys
import json
from google_slides_client import GoogleSlidesClient
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_google_slides():
    client = None
    presentation_id = None
    
    try:
        # Inicializar cliente
        logger.info("Iniciando teste do Google Slides...")
        client = GoogleSlidesClient(
            credentials_path=Config.GOOGLE_CREDENTIALS_JSON,
            template_presentation_id=Config.TEMPLATE_PRESENTATION_ID
        )
        
        # Verificar template
        logger.info("Verificando template...")
        template_info = client.get_template_info()
        logger.info("Estrutura do template:")
        logger.info(json.dumps(template_info, indent=2))
        
        if not client.verify_template_exists():
            raise Exception("Template não encontrado")
            
        # Carregar dados do JSON
        json_file = "output/slides_data.json"
        logger.info(f"Carregando dados do arquivo: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            slides_data = json.load(f)
            
        # Validar IDs dos elementos
        logger.info("Validando IDs dos elementos...")
        template_elements = template_info.get('slideElements', [])
        template_ids = [elem.get('objectId') for elem in template_elements]
        
        # Validar cada seção do JSON
        for section in slides_data:
            if isinstance(section, dict) and 'elements' in section:
                for element_id in section['elements'].keys():
                    if element_id not in template_ids:
                        logger.warning(f"ID não encontrado no template: {element_id}")
        
        # Debug: Mostrar estrutura dos dados
        logger.info("Dados do JSON a serem inseridos:")
        logger.info(json.dumps(slides_data, indent=2))
        
        # Criar apresentação com dados do JSON
        logger.info("Criando apresentação a partir dos dados...")
        presentation_id = client.create_slides_from_json(slides_data)
        
        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        logger.info(f"Apresentação criada com sucesso: {presentation_url}")
        
        return {
            "success": True,
            "presentation_id": presentation_id,
            "url": presentation_url
        }
        
    except FileNotFoundError as e:
        error_msg = f"Arquivo JSON não encontrado: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "presentation_id": None
        }
    except json.JSONDecodeError as e:
        error_msg = f"Erro ao decodificar JSON: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "presentation_id": None
        }
    except Exception as e:
        error_msg = f"Erro ao testar Google Slides: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "presentation_id": presentation_id
        }
        
    finally:
        if presentation_id:
            presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
            logger.info(f"Link da apresentação criada: {presentation_url}")

if __name__ == "__main__":
    result = test_google_slides()
    sys.exit(0 if result["success"] else 1)