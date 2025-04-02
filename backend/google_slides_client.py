import uuid
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleSlidesClient:
    def __init__(self, credentials_path, template_presentation_id):
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
        drive_service = self._get_service('drive', 'v3')
        new_presentation = drive_service.files().copy(
            fileId=self.template_presentation_id,
            body={'name': f"Relatório Genético - {uuid.uuid4()}"}
        ).execute()
        
        drive_service.permissions().create(
            fileId=new_presentation['id'],
            body={'type': 'anyone', 'role': 'writer'}
        ).execute()
        
        return new_presentation['id']

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

        # Cria uma nova apresentação a partir do template
        presentation_id = self.create_new_slide_by_template()

        # Adiciona slides com base no conteúdo do JSON
        slides_service = self._get_service('slides', 'v1')
        requests = []

        for page in data["pages"]:
            slide_content = page["markdown"]
            slide_images = page.get("images", [])

            # Adiciona um slide em branco
            slide_id = f"slide_{uuid.uuid4().hex[:8]}"
            requests.append({
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": "1",
                    "slideLayoutReference": {
                        "predefinedLayout": "TITLE_AND_BODY"
                    }
                }
            })

            # Adiciona texto ao slide
            requests.append({
                "insertText": {
                    "objectId": slide_id,
                    "text": slide_content,
                    "insertionIndex": 0
                }
            })

            # Adiciona imagens ao slide
            for image in slide_images:
                image_url = image.get("image_base64") or f"https://example.com/{image['id']}"
                requests.append({
                    "createImage": {
                        "objectId": f"image_{uuid.uuid4().hex[:8]}",
                        "url": image_url,
                        "elementProperties": {
                            "pageObjectId": slide_id,
                            "size": {
                                "height": {"magnitude": 3000000, "unit": "EMU"},
                                "width": {"magnitude": 3000000, "unit": "EMU"}
                            },
                            "transform": {
                                "scaleX": 1,
                                "scaleY": 1,
                                "translateX": 1000000,
                                "translateY": 1000000,
                                "unit": "EMU"
                            }
                        }
                    }
                })

        # Executa as requisições para criar os slides
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()

        return f"https://docs.google.com/presentation/d/{presentation_id}/edit"