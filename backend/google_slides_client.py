import uuid
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

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

    def create_slides_from_json(self, json_path):
        """Cria slides no Google Slides com base no conteúdo do JSON."""
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Cria nova apresentação
        presentation_id = self.create_new_slide_by_template()
        slides_service = self._get_service('slides', 'v1')
        
        # Preparar requisições para criar slides
        requests = []
        
        # Slide de título
        requests.append({
            "createSlide": {
                "objectId": f"slide_title",
                "slideLayoutReference": {"predefinedLayout": "TITLE"}
            }
        })
        
        # Criar slides para cada seção
        for section in data:
            slide_id = f"slide_{uuid.uuid4().hex[:8]}"
            
            # Definir layout baseado no tipo de seção
            layout = "TITLE_AND_BODY"
            if section.get("type") == "genetic_section":
                layout = "TWO_COLUMNS"
            
            # Criar slide
            requests.append({
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": layout}
                }
            })
            
            # Adicionar título
            if section.get("title"):
                requests.append({
                    "insertText": {
                        "objectId": f"{slide_id}_title",
                        "text": section["title"]
                    }
                })
            
            # Adicionar conteúdo
            if section.get("content"):
                requests.append({
                    "insertText": {
                        "objectId": f"{slide_id}_body",
                        "text": section["content"]
                    }
                })

        # Executar todas as requisições
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()

        return f"https://docs.google.com/presentation/d/{presentation_id}/edit"