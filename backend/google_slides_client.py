import uuid
import json
import os
import logging
import time
from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pdfplumber
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)

def get_service(credentials, scopes, service_build, service_version):
    creds = service_account.Credentials.from_service_account_file(
        credentials, scopes=[scopes] if isinstance(scopes, str) else scopes
    )
    return build(service_build, service_version, credentials=creds)

class GoogleSlidesClient:
    def __init__(self, credentials_path, template_presentation_id):
        # Adiciona checagem para evitar uso do client_id como template_id
        if template_presentation_id and len(template_presentation_id) < 30:
            raise ValueError("O template_presentation_id parece inválido. Use o ID de uma apresentação do Google Slides, não o client_id das credenciais.")
        if not template_presentation_id:
            raise ValueError("Você deve fornecer um template_presentation_id válido ao instanciar GoogleSlidesClient.")
        self.credentials = credentials_path
        self.template_presentation_id = template_presentation_id
        # Inicializa os serviços Google Slides e Drive
        self.service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/presentations',
            service_build='slides',
            service_version='v1'
        )
        self.drive_service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/drive',
            service_build='drive',
            service_version='v3'
        )

    def create_new_slide_by_template(self):
        if not self.template_presentation_id:
            raise ValueError("template_presentation_id não definido. Defina um ID de template válido ao instanciar GoogleSlidesClient.")
        name_new_presentation = str(uuid.uuid4())
        drive_service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/drive',
            service_build='drive',
            service_version='v3'
        )
        dict_new_presentation = {"name": name_new_presentation}
        print(f"Copying template {self.template_presentation_id} and creating new the presentation {name_new_presentation}")
        new_presentation_id = drive_service.files().copy(body=dict_new_presentation, fileId=self.template_presentation_id).execute()['id']

        permissions_request_body = {
            "role": "reader",
            "type": "anyone"
        }
        drive_service.permissions().create(
            fileId=new_presentation_id,
            body=permissions_request_body
        ).execute()
        print(f"New presentation id {new_presentation_id}")
        return new_presentation_id

    def text_replace(self, key: str, replace_text: str, presentation_id: str, pages: list = []):
        service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/presentations',
            service_build='slides',
            service_version='v1'
        )
        service.presentations().batchUpdate(
            body={
                "requests": [
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": '{{' + key + '}}'
                            },
                            "replaceText": replace_text,
                            "pageObjectIds": pages,
                        }
                    }
                ]
            },
            presentationId=presentation_id
        ).execute()

    def replace_shape_with_image(self, url: str, presentation_id: str, key: str = None, pages: list = []):
        service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/presentations',
            service_build='slides',
            service_version='v1'
        )
        service.presentations().batchUpdate(
            body={
                "requests": [
                    {
                        "replaceAllShapesWithImage": {
                            "imageUrl": url,
                            "replaceMethod": "CENTER_INSIDE",
                            "containsText": {
                                "text": "{{" + key + "}}",
                            },
                            "pageObjectIds": pages
                        }
                    }
                ]
            },
            presentationId=presentation_id
        ).execute()

    def duplicate_slide(self, presentation_id: str, page_id: str, new_page_ids: list):
        service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/presentations',
            service_build='slides',
            service_version='v1'
        )
        requests = []
        for id in new_page_ids[::-1]:
            obj = {page_id: id}
            requests.append({'duplicateObject': {'objectId': page_id, 'objectIds': obj}})
        # Uncomment the following line if you want to delete the original slide
        # requests.append({'deleteObject': {'objectId': page_id}})
        service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': requests}).execute()

    def move_slide(self, presentation_id: str, num_page_target: str, list_page_id_to_move: list):
        service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/presentations',
            service_build='slides',
            service_version='v1'
        )
        requests = []
        requests.append({
            "updateSlidesPosition": {
                "slideObjectIds": list_page_id_to_move,
                "insertionIndex": num_page_target
            }
        })
        service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': requests}).execute()

    def add_speaker_notes(self, presentation_id: str, slide_id: str, speaker_notes_text: str):
        service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/presentations',
            service_build='slides',
            service_version='v1'
        )
        presentation = service.presentations().get(presentationId=presentation_id).execute()
        slides = presentation.get('slides')
        speaker_notes_id = None
        for slide in slides:
            if slide['objectId'] == slide_id:
                speaker_notes_id = slide['slideProperties']['notesPage']['notesProperties']['speakerNotesObjectId']
                break
        requests = [
            {
                'insertText': {
                    'objectId': speaker_notes_id,
                    'insertionIndex': 0,
                    'text': speaker_notes_text,
                }
            }
        ]
        service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()

    def create_slides_from_structured_json(self, json_path: str) -> str:
        """
        Cria slides no Google Slides a partir de um arquivo JSON estruturado (dados_estruturado.json).
        Cada página do JSON vira um slide, com título, texto, tabelas e imagens.
        """
        with open(json_path, encoding="utf-8") as f:
            dados = json.load(f)
        paginas = dados["paginas"]

        # Cria nova apresentação a partir do template
        presentation_id = self.create_new_slide_by_template()

        service = get_service(
            credentials=self.credentials,
            scopes='https://www.googleapis.com/auth/presentations',
            service_build='slides',
            service_version='v1'
        )

        # Recupera slides existentes (para saber o id do slide inicial)
        presentation = service.presentations().get(presentationId=presentation_id).execute()
        slides = presentation.get('slides', [])
        if slides:
            first_slide_id = slides[0]['objectId']
        else:
            first_slide_id = None

        # Para cada página do JSON, duplica o slide do template e faz replace
        for idx, pagina in enumerate(paginas):
            # Duplicar slide base (primeiro slide do template)
            new_slide_id = f"slide_{uuid.uuid4().hex[:8]}"
            self.duplicate_slide(presentation_id, first_slide_id, [new_slide_id])

            # Substituir textos
            if pagina.get("titulo"):
                self.text_replace("TITULO", pagina["titulo"], presentation_id, [new_slide_id])
            if pagina.get("texto"):
                self.text_replace("TEXTO", pagina["texto"], presentation_id, [new_slide_id])

            # Substituir tabelas (como texto formatado)
            if pagina.get("tabelas"):
                for tabela in pagina["tabelas"]:
                    tabela_txt = ""
                    if tabela.get("cabecalho"):
                        tabela_txt += " | ".join(tabela["cabecalho"]) + "\n"
                        tabela_txt += "-|-".join(["-" for _ in tabela["cabecalho"]]) + "\n"
                    for linha in tabela.get("linhas", []):
                        tabela_txt += " | ".join(str(x) for x in linha) + "\n"
                    self.text_replace("TABELA", tabela_txt, presentation_id, [new_slide_id])

            # Substituir imagens (se houver URL pública ou lógica para upload)
            # for img_idx, img in enumerate(pagina.get("imagens", [])):
            #     image_url = img.get("url")  # Adapte para sua lógica de URL
            #     if image_url:
            #         self.replace_shape_with_image(image_url, presentation_id, key="IMAGEM", pages=[new_slide_id])

        # Opcional: remover slide base/template do início
        if first_slide_id:
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': [{'deleteObject': {'objectId': first_slide_id}}]}
            ).execute()

        return presentation_id

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
            # Garantir que json_data seja um objeto Python
            if isinstance(json_data, str):
                try:
                    data = json.loads(json_data)
                except json.JSONDecodeError:
                    raise ValueError("JSON inválido fornecido")
            else:
                data = json_data

            # Validar estrutura dos dados
            if not isinstance(data, (list, dict)):
                raise ValueError("Dados devem ser uma lista ou dicionário")

            # Converter para lista se for dicionário
            if isinstance(data, dict):
                data = [data]
                
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

    def get_first_slide_id(self, presentation_id: str) -> str:
        """Get the ID of the first slide in the presentation"""
        try:
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            if presentation.get('slides'):
                return presentation['slides'][0]['objectId']
            return ''
            
        except Exception as e:
            logger.error(f"Error getting first slide ID: {str(e)}")
            return ''

    def create_presentation_from_pdf(self, pdf_path: str) -> str:
        """
        Cria uma apresentação no Google Slides replicando cada página do PDF como um slide.
        """
        slides_service = self._get_service('slides', 'v1')
        drive_service = self._get_service('drive', 'v3')

        # Cria uma nova apresentação
        presentation = slides_service.presentations().create(
            body={'title': f"Apresentação PDF - {uuid.uuid4()}"}
        ).execute()

        # Permite acesso por link
        drive_service.permissions().create(
            fileId=presentation['presentationId'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        # Remove slide inicial em branco
        first_slide_id = presentation['slides'][0]['objectId']
        slides_service.presentations().batchUpdate(
            presentationId=presentation['presentationId'],
            body={'requests': [{'deleteObject': {'objectId': first_slide_id}}]}
        ).execute()

        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages):
                slide_id = f"slide_{uuid.uuid4().hex[:8]}"
                # Cria slide em branco
                slides_service.presentations().batchUpdate(
                    presentationId=presentation['presentationId'],
                    body={'requests': [{
                        "createSlide": {
                            "objectId": slide_id,
                            "insertionIndex": idx,
                            "slideLayoutReference": {"predefinedLayout": "BLANK"}
                        }
                    }]}
                ).execute()

                # Extrai texto
                text = page.extract_text() or ""
                if text.strip():
                    # Adiciona caixa de texto centralizada
                    text_box_id = f"{slide_id}_text"
                    slides_service.presentations().batchUpdate(
                        presentationId=presentation['presentationId'],
                        body={'requests': [
                            {
                                "createShape": {
                                    "objectId": text_box_id,
                                    "shapeType": "TEXT_BOX",
                                    "elementProperties": {
                                        "pageObjectId": slide_id,
                                        "size": {"height": {"magnitude": 300, "unit": "PT"}, "width": {"magnitude": 600, "unit": "PT"}},
                                        "transform": {
                                            "scaleX": 1, "scaleY": 1, "translateX": 50, "translateY": 100, "unit": "PT"
                                        }
                                    }
                                }
                            },
                            {
                                "insertText": {
                                    "objectId": text_box_id,
                                    "insertionIndex": 0,
                                    "text": text
                                }
                            }
                        ]}
                    ).execute()

                # Extrai imagens
                for img_idx, img in enumerate(page.images):
                    x0, top, x1, bottom = img["x0"], img["top"], img["x1"], img["bottom"]
                    # Recorta imagem da página
                    pil_img = page.to_image(resolution=200).original.crop((x0, top, x1, bottom))
                    buffered = io.BytesIO()
                    pil_img.save(buffered, format="PNG")
                    img_b64 = base64.b64encode(buffered.getvalue()).decode()
                    image_url = f"data:image/png;base64,{img_b64}"

                    image_id = f"{slide_id}_img_{img_idx}"
                    slides_service.presentations().batchUpdate(
                        presentationId=presentation['presentationId'],
                        body={'requests': [
                            {
                                "createImage": {
                                    "objectId": image_id,
                                    "url": image_url,
                                    "elementProperties": {
                                        "pageObjectId": slide_id,
                                        "size": {"height": {"magnitude": 200, "unit": "PT"}, "width": {"magnitude": 300, "unit": "PT"}},
                                        "transform": {
                                            "scaleX": 1, "scaleY": 1, "translateX": 100 + img_idx*320, "translateY": 420, "unit": "PT"
                                        }
                                    }
                                }
                            }
                        ]}
                    ).execute()

        return presentation['presentationId']

    def create_slides_from_structured_json(self, json_path: str) -> str:
        """
        Cria slides no Google Slides a partir de um arquivo JSON estruturado (dados_estruturado.json).
        Cada página do JSON vira um slide, com título, texto, tabelas e imagens.
        """
        # Carregar o JSON estruturado
        with open(json_path, encoding="utf-8") as f:
            dados = json.load(f)
        paginas = dados["paginas"]

        slides_service = self._get_service('slides', 'v1')
        drive_service = self._get_service('drive', 'v3')

        # Cria uma nova apresentação
        presentation = slides_service.presentations().create(
            body={'title': f"Relatório Genético Estruturado - {uuid.uuid4()}"}
        ).execute()

        # Permite acesso por link
        drive_service.permissions().create(
            fileId=presentation['presentationId'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        # Remove slide inicial em branco
        first_slide_id = presentation['slides'][0]['objectId']
        slides_service.presentations().batchUpdate(
            presentationId=presentation['presentationId'],
            body={'requests': [{'deleteObject': {'objectId': first_slide_id}}]}
        ).execute()

        # Cria slides para cada página do JSON
        for idx, pagina in enumerate(paginas):
            slide_id = f"slide_{uuid.uuid4().hex[:8]}"
            # Escolhe layout: título + corpo se houver texto, senão só título
            layout = "TITLE_AND_BODY" if pagina.get("texto") else "TITLE"
            slides_service.presentations().batchUpdate(
                presentationId=presentation['presentationId'],
                body={'requests': [{
                    "createSlide": {
                        "objectId": slide_id,
                        "insertionIndex": idx,
                        "slideLayoutReference": {"predefinedLayout": layout}
                    }
                }]}
            ).execute()

            # Busca elementos do slide para inserir texto
            slide = slides_service.presentations().pages().get(
                presentationId=presentation['presentationId'],
                pageObjectId=slide_id
            ).execute()

            title_id = None
            body_id = None
            for el in slide.get("pageElements", []):
                shape = el.get("shape", {})
                if shape.get("shapeType") == "TITLE":
                    title_id = el["objectId"]
                elif shape.get("shapeType") in ["BODY", "TEXT_BOX"]:
                    body_id = el["objectId"]

            # Insere título
            if title_id and pagina.get("titulo"):
                slides_service.presentations().batchUpdate(
                    presentationId=presentation['presentationId'],
                    body={'requests': [{
                        "insertText": {
                            "objectId": title_id,
                            "insertionIndex": 0,
                            "text": pagina["titulo"]
                        }
                    }]}
                ).execute()

            # Insere texto
            if body_id and pagina.get("texto"):
                slides_service.presentations().batchUpdate(
                    presentationId=presentation['presentationId'],
                    body={'requests': [{
                        "insertText": {
                            "objectId": body_id,
                            "insertionIndex": 0,
                            "text": pagina["texto"]
                        }
                    }]}
                ).execute()

            # Insere tabelas (como texto formatado, para simplicidade)
            if body_id and pagina.get("tabelas"):
                for tabela in pagina["tabelas"]:
                    tabela_txt = ""
                    if tabela.get("cabecalho"):
                        tabela_txt += " | ".join(tabela["cabecalho"]) + "\n"
                        tabela_txt += "-|-".join(["-" for _ in tabela["cabecalho"]]) + "\n"
                    for linha in tabela.get("linhas", []):
                        tabela_txt += " | ".join(str(x) for x in linha) + "\n"
                    slides_service.presentations().batchUpdate(
                        presentationId=presentation['presentationId'],
                        body={'requests': [{
                            "insertText": {
                                "objectId": body_id,
                                "insertionIndex": 0,
                                "text": tabela_txt + "\n"
                            }
                        }]}
                    ).execute()

            # Insere imagens (apenas se URLs públicas ou data URI, ajuste conforme necessário)
            for img_idx, img in enumerate(pagina.get("imagens", [])):
                image_id = f"{slide_id}_img_{img_idx}"
                # Aqui espera-se que você tenha a URL da imagem ou data URI
                # Exemplo: image_url = img["url"]
                # Se não tiver, pule ou adapte para buscar a imagem localmente e fazer upload para um bucket público
                # slides_service.presentations().batchUpdate(
                #     presentationId=presentation['presentationId'],
                #     body={'requests': [{
                #         "createImage": {
                #             "objectId": image_id,
                #             "url": image_url,
                #             "elementProperties": {
                #                 "pageObjectId": slide_id,
                #                 "size": {"height": {"magnitude": 200, "unit": "PT"}, "width": {"magnitude": 300, "unit": "PT"}},
                #                 "transform": {
                #                     "scaleX": 1, "scaleY": 1, "translateX": 100 + img_idx*320, "translateY": 420, "unit": "PT"
                #                 }
                #             }
                #         }
                #     }]}
                # ).execute()
                pass  # Implemente se tiver URLs de imagens

        return presentation['presentationId']