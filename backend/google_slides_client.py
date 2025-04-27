import uuid
import json
import os
import logging
import time
from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GoogleSlidesClient:
    def __init__(self, credentials_path, template_presentation_id=None):
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Google credentials file not found at: {credentials_path}. "
                "Make sure the credentials file exists and the path is correct."
            )
        self.credentials_path = credentials_path
        self.template_presentation_id = template_presentation_id
        self.scopes = [
            'https://www.googleapis.com/auth/presentations',
            'https://www.googleapis.com/auth/drive'
        ]
        self.service = self._get_service('slides', 'v1')
        self.drive_service = self._get_service('drive', 'v3')
        
    def _get_service(self, service_name, version):
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=self.scopes
        )
        return build(service_name, version, credentials=creds)

    def create_new_slide_by_template(self):
        """Create a new presentation instead of copying a template"""
        slides_service = self._get_service('slides', 'v1')
        drive_service = self._get_service('drive', 'v3')
        
        # Create a new blank presentation
        presentation = slides_service.presentations().create(
            body={'title': f"Relatório Genético - {uuid.uuid4()}"}
        ).execute()
        
        # Set permissions to anyone with the link can view
        drive_service.permissions().create(
            fileId=presentation['presentationId'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        # Add initial slides and content
        requests = [
            {
                'createSlide': {
                    'objectId': 'titleSlide',
                    'insertionIndex': '0',
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE'
                    }
                }
            },
            {
                'insertText': {
                    'objectId': 'titleSlide',
                    'insertionIndex': 0,
                    'text': 'Relatório de Análise Genética'
                }
            }
        ]
        
        # Create the slide first
        response = slides_service.presentations().batchUpdate(
            presentationId=presentation['presentationId'],
            body={'requests': requests[:1]}  # Only create slide first
        ).execute()
        
        # Get the title element ID from the created slide
        slide = slides_service.presentations().pages().get(
            presentationId=presentation['presentationId'],
            pageObjectId='titleSlide'
        ).execute()
        
        # Find the title element ID
        title_element_id = None
        for element in slide.get('pageElements', []):
            if element.get('shape', {}).get('shapeType') == 'TEXT_BOX':
                title_element_id = element['objectId']
                break
        
        if title_element_id:
            # Now insert the text into the title element
            text_request = {
                'insertText': {
                    'objectId': title_element_id,
                    'insertionIndex': 0,
                    'text': 'Relatório de Análise Genética'
                }
            }
            
            slides_service.presentations().batchUpdate(
                presentationId=presentation['presentationId'],
                body={'requests': [text_request]}
            ).execute()
        
        return presentation['presentationId']

    def add_slide(self, presentation_id, template_page_id):
        slides_service = self._get_service('slides', 'v1')
        
        request = {
            "createSlide": {
                "objectId": f"slide_{uuid.uuid4().hex[:8]}",
                "insertionIndex": 1,
                "slideLayoutReference": {
                    "predefinedLayout": "BLANK"
                },
                "placeholderIdMappings": [{
                    "objectId": template_page_id,
                    "layoutPlaceholder": {
                        "type": "BODY",
                        "index": 0
                    }
                }]
            }
        }
        
        response = slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': [request]}
        ).execute()
        
        return response['replies'][0]['createSlide']['objectId']

    def text_replace(self, presentation_id, replacements, page_ids):
        slides_service = self._get_service('slides', 'v1')
        
        requests = []
        for key, value in replacements.items():
            requests.append({
                'replaceAllText': {
                    'containsText': {'text': f'{{{{{key}}}}}'},
                    'replaceText': value,
                    'pageObjectIds': page_ids
                }
            })
        
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()

    def _batch_requests(self, presentation_id: str, requests: List[Dict[str, Any]], batch_size: int = 10) -> None:
        """Execute requests in batches with rate limiting"""
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            retries = 3
            while retries > 0:
                try:
                    self.service.presentations().batchUpdate(
                        presentationId=presentation_id,
                        body={"requests": batch}
                    ).execute()
                    # Wait 1.5 seconds between batches to stay under rate limit
                    time.sleep(1.5)
                    break
                except Exception as e:
                    if 'RATE_LIMIT_EXCEEDED' in str(e) and retries > 1:
                        wait_time = (4 - retries) * 2  # Progressive backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        retries -= 1
                    else:
                        raise

    def create_slides_from_json(self, json_data):
        """Cria slides no Google Slides com base no conteúdo do JSON."""
        try:
            data = json.loads(json_data) if isinstance(json_data, str) else json_data
            presentation_id = self.create_new_slide_by_template()
            
            # First batch: Create all slides
            create_requests = []
            slide_ids = []  # Store slide IDs for later use
            
            for index, section in enumerate(data):
                slide_id = f"slide_{uuid.uuid4().hex[:8]}"
                slide_ids.append(slide_id)
                layout = self._determine_layout(section)
                
                create_requests.append({
                    "createSlide": {
                        "objectId": slide_id,
                        "insertionIndex": index + 1,  # +1 to skip title slide
                        "slideLayoutReference": {"predefinedLayout": layout}
                    }
                })
            
            # Execute slide creation requests
            if create_requests:
                self._batch_requests(presentation_id, create_requests)
                
            # Second batch: Get slide details and insert text
            for slide_id, section in zip(slide_ids, data):
                # Get slide details to find element IDs
                slide = self.service.presentations().pages().get(
                    presentationId=presentation_id,
                    pageObjectId=slide_id
                ).execute()
                
                text_requests = []
                
                # Find title and body elements
                for element in slide.get('pageElements', []):
                    if 'shape' in element and 'objectId' in element:
                        shape_type = element['shape'].get('shapeType', '')
                        element_id = element['objectId']
                        
                        if shape_type == 'TITLE' and section.get('title'):
                            text_requests.append({
                                'insertText': {
                                    'objectId': element_id,
                                    'text': section['title']
                                }
                            })
                        elif shape_type in ['BODY', 'TEXT_BOX'] and section.get('content'):
                            text_requests.append({
                                'insertText': {
                                    'objectId': element_id,
                                    'text': self._format_content(section['content'])
                                }
                            })
                
                # Execute text insertion requests for this slide
                if text_requests:
                    self._batch_requests(presentation_id, text_requests)
            
            return presentation_id
            
        except Exception as e:
            logger.error(f"Erro ao criar slides: {str(e)}")
            raise

    def _determine_layout(self, section):
        """Determina o melhor layout baseado no conteúdo da seção"""
        if not section.get("title") and not section.get("content"):
            return "BLANK"
        if "|" in section.get("content", ""):  # Tem tabela
            return "TITLE_AND_BODY"
        if section.get("images"):
            return "TITLE_AND_TWO_COLUMNS"
        return "SECTION_HEADER"  # Default

    def _format_content(self, content):
        """Formata o conteúdo para apresentação"""
        # Remove marcações markdown básicas
        content = content.replace("## ", "")
        content = content.replace("# ", "")
        content = content.replace("**", "")
        content = content.replace("*", "")
        return content.strip()

    def _create_table_requests(self, slide_id, content):
        """Cria requests para tabelas"""
        requests = []
        # Identificar linhas da tabela
        table_lines = [line.strip() for line in content.split("\n") if "|" in line]
        if not table_lines:
            return requests
            
        # Calcular dimensões da tabela
        rows = len(table_lines)
        cols = len(table_lines[0].split("|")) - 2  # -2 para remover bordas vazias
        
        # Adicionar request de criação de tabela
        requests.append({
            "createTable": {
                "objectId": f"{slide_id}_table",
                "rows": rows,
                "columns": cols,
                "location": {
                    "x": 100,  # Posição x na slide
                    "y": 200   # Posição y na slide
                }
            }
        })
        
        return requests

    def _create_text_request(self, slide_id, element_type, text):
        """Helper to create text insertion request"""
        return {
            "insertText": {
                "objectId": f"{slide_id}_{element_type}",
                "text": text
            }
        }

    def _create_image_request(self, slide_id, image_data):
        """Helper to create image insertion request"""
        # Add image handling logic here
        pass
    
    def verify_template_exists(self) -> bool:
        """Verifica se o template existe e está acessível"""
        try:
            if not self.template_presentation_id:
                # Se não há template, consideramos como sucesso
                return True
                
            self.service.presentations().get(
                presentationId=self.template_presentation_id
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar template: {str(e)}")
            return False
    
    def verify_slide_exists(self, presentation_id: str, slide_id: str) -> bool:
        """Verifica se um slide específico existe na apresentação"""
        try:
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            for slide in presentation.get('slides', []):
                if slide.get('objectId') == slide_id:
                    return True
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar slide: {str(e)}")
            return False
    
    def delete_presentation(self, presentation_id: str) -> bool:
        """Remove uma apresentação"""
        try:
            self.drive_service.files().delete(
                fileId=presentation_id
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar apresentação: {str(e)}")
            return False

    def get_template_info(self):
        """Obtém informações sobre a estrutura do template."""
        try:
            presentation = self.service.presentations().get(
                presentationId=self.template_presentation_id
            ).execute()
            
            # Extrair informações relevantes
            template_info = {
                'presentationId': presentation.get('presentationId'),
                'title': presentation.get('title'),
                'slideElements': []  # Lista plana de IDs de elementos
            }
            
            # Processar cada slide
            for slide in presentation.get('slides', []):
                # Processar elementos do slide
                for element in slide.get('pageElements', []):
                    if 'objectId' in element:
                        template_info['slideElements'].append({
                            'objectId': element.get('objectId'),
                            'type': element.get('shape', {}).get('shapeType', 'OTHER')
                        })
            
            return template_info
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do template: {str(e)}")
            raise