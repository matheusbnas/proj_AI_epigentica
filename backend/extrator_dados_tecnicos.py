#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extrator de Dados Técnicos de Catálogos (Versão Ajustada)
Projeto Xartam - Extração de dados técnicos de catálogos em PDF para JSON

Este script utiliza o Mistral OCR e técnicas de processamento de imagem para extrair 
dados técnicos de catálogos em PDF, incluindo textos e imagens, e salvar em formato JSON.

Suporte multilíngue: português, inglês e chinês.
"""

import os
import json
import time
import logging
import re
import base64
import tempfile
from typing import Dict, List, Any, Optional, Tuple
import argparse
from mistralai import Mistral, DocumentURLChunk
import cv2
import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extrator_dados.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ExtratorDadosTecnicos:
    """
    Classe para extração de dados técnicos de catálogos em PDF e conversão para JSON.
    Versão ajustada para extrair textos e imagens de catálogos de peças e manuais técnicos.
    """

    def __init__(self, api_key: str, output_dir: str = "output", figs_dir: str = "figs"):
        """
        Inicializa o extrator de dados técnicos.

        Args:
            api_key: Chave de API do Mistral
            output_dir: Diretório de saída para os arquivos JSON
            figs_dir: Diretório de saída para as imagens extraídas
        """
        self.client = Mistral(api_key=api_key)
        self.output_dir = output_dir
        self.figs_dir = figs_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.figs_dir, exist_ok=True)

    def processar_arquivo(self, arquivo_pdf: str) -> Dict[str, Any]:
        """
        Processa um arquivo PDF para extrair textos e imagens.

        Args:
            arquivo_pdf: Caminho para o arquivo PDF

        Returns:
            Dicionário com os dados extraídos
        """
        logger.info(f"Processando arquivo: {arquivo_pdf}")

        # Verificar se o arquivo existe
        if not os.path.exists(arquivo_pdf):
            logger.error(f"Arquivo não encontrado: {arquivo_pdf}")
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_pdf}")

        # Upload do arquivo para o Mistral OCR
        try:
            uploaded_file = self.client.files.upload(
                file={
                    "file_name": os.path.basename(arquivo_pdf),
                    "content": open(arquivo_pdf, "rb")
                },
                purpose="ocr"
            )
            logger.info(f"Arquivo enviado com sucesso. ID: {uploaded_file.id}")

            # Obter URL assinada para o arquivo enviado
            signed_url = self.client.files.get_signed_url(
                file_id=uploaded_file.id,
                expiry=1  # Tempo de expiração em horas
            )

            # Processar OCR para extrair texto e imagens
            ocr_result = self.client.ocr.process(
                model="mistral-ocr-latest",
                document=DocumentURLChunk(document_url=signed_url.url)
            )

            # Converter o resultado para um dicionário
            ocr_result_dict = ocr_result.model_dump()

            # Extrair e processar os dados
            dados_processados = self.processar_resultado_ocr(
                ocr_result_dict, arquivo_pdf)

            # Salvar o resultado em um arquivo JSON
            output_file = os.path.join(
                self.output_dir, f"{os.path.splitext(os.path.basename(arquivo_pdf))[0]}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(dados_processados, f, indent=4, ensure_ascii=False)
                logger.info(f"Dados extraídos salvos em: {output_file}")

            return dados_processados

        except Exception as e:
            logger.error(f"Erro ao processar o arquivo: {str(e)}")
            raise

    def processar_resultado_ocr(self, ocr_result: Dict[str, Any], arquivo_pdf: str) -> Dict[str, Any]:
        """
        Processa o resultado do OCR para extrair textos e imagens.

        Args:
            ocr_result: Resultado do OCR em formato de dicionário
            arquivo_pdf: Caminho para o arquivo PDF original

        Returns:
            Dicionário com os dados processados
        """
        logger.info("Processando resultado do OCR...")

        # Extrair informações básicas
        nome_arquivo = os.path.basename(arquivo_pdf)

        # Estrutura para armazenar os dados processados
        dados_processados = {
            "arquivo": nome_arquivo,
            "data_processamento": time.strftime("%Y-%m-%d %H:%M:%S"),
            "paginas": []
        }

        # Processar cada página
        for page_idx, page in enumerate(ocr_result.get("pages", [])):
            logger.info(f"Processando página {page_idx+1}")

            # Extrair texto da página
            texto_pagina = ""
            if "markdown" in page:
                # Remover referências a imagens do markdown
                texto_pagina = re.sub(r'!\[.*?\]\(.*?\)', '', page["markdown"])

            # Estrutura para armazenar informações da página
            info_pagina = {
                "numero": page_idx + 1,
                "texto": texto_pagina.strip(),
                "imagens": []
            }

            # Processar imagens da página
            for img_idx, img in enumerate(page.get("images", [])):
                # Extrair informações da imagem
                img_info = {
                    "id": f"img_{page_idx+1}_{img_idx+1}",
                    "posicao": {
                        "top_left_x": img.get("top_left_x", 0),
                        "top_left_y": img.get("top_left_y", 0),
                        "bottom_right_x": img.get("bottom_right_x", 0),
                        "bottom_right_y": img.get("bottom_right_y", 0)
                    }
                }

                # Se a imagem tiver dados base64, salvar a imagem e extrair texto
                if img.get("image_base64"):
                    # Salvar a imagem
                    img_path = self.salvar_imagem(
                        img["image_base64"],
                        os.path.splitext(nome_arquivo)[0],
                        page_idx,
                        img_idx
                    )

                    if img_path:
                        img_info["caminho_arquivo"] = os.path.relpath(
                            img_path, start=os.getcwd())

                        # Extrair texto da imagem
                        texto_imagem = self.extrair_texto_imagem(img_path)
                        if texto_imagem:
                            img_info["texto_extraido"] = texto_imagem

                # Adicionar informações da imagem à página
                info_pagina["imagens"].append(img_info)

            # Adicionar informações da página aos dados processados
            dados_processados["paginas"].append(info_pagina)

        return dados_processados

    def salvar_imagem(self, image_base64: str, nome_base: str, page_idx: int, img_idx: int) -> Optional[str]:
        """
        Salva uma imagem a partir de dados base64.

        Args:
            image_base64: Dados da imagem em formato base64
            nome_base: Nome base para o arquivo de imagem
            page_idx: Índice da página
            img_idx: Índice da imagem

        Returns:
            Caminho para o arquivo de imagem salvo ou None se falhar
        """
        try:
            # Decodificar a imagem base64
            img_data = base64.b64decode(image_base64)

            # Converter para formato numpy para processamento com OpenCV
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                logger.warning("Falha ao decodificar imagem")
                return None

            # Criar nome de arquivo para a imagem
            img_filename = f"{nome_base}_pagina_{page_idx+1}_img_{img_idx+1}.png"
            img_path = os.path.join(self.figs_dir, img_filename)

            # Salvar a imagem
            cv2.imwrite(img_path, img)
            logger.info(f"Imagem salva em: {img_path}")

            return img_path

        except Exception as e:
            logger.error(f"Erro ao salvar imagem: {str(e)}")
            return None

    def extrair_texto_imagem(self, img_path: str) -> Optional[str]:
        """
        Extrai texto de uma imagem usando OCR.

        Args:
            img_path: Caminho para o arquivo de imagem

        Returns:
            Texto extraído da imagem ou None se falhar
        """
        logger.info(f"Extraindo texto da imagem: {img_path}")

        try:
            # Upload da imagem para o Mistral
            uploaded_file = self.client.files.upload(
                file={
                    "file_name": os.path.basename(img_path),
                    "content": open(img_path, "rb")
                },
                purpose="ocr"
            )

            # Obter URL assinada para a imagem enviada
            signed_url = self.client.files.get_signed_url(
                file_id=uploaded_file.id,
                expiry=1  # Tempo de expiração em horas
            )

            # Processar OCR para extrair texto da imagem
            ocr_result = self.client.ocr.process(
                model="mistral-ocr-latest",
                document=DocumentURLChunk(document_url=signed_url.url)
            )

            # Converter o resultado para um dicionário
            ocr_result_dict = ocr_result.model_dump()

            # Extrair texto da imagem
            texto = ""
            if "text" in ocr_result_dict:
                texto = ocr_result_dict.get("text", "")
            else:
                # Se não houver texto diretamente, tentar extrair de cada página
                for page in ocr_result_dict.get("pages", []):
                    if "markdown" in page:
                        # Remover referências a imagens do markdown
                        texto_pagina = re.sub(
                            r'!\[.*?\]\(.*?\)', '', page["markdown"])
                        texto += texto_pagina + "\n\n"

            if texto.strip():
                logger.info(f"Texto extraído da imagem: {texto[:100]}...")
                return texto.strip()
            else:
                logger.warning("Nenhum texto extraído da imagem")
                return None

        except Exception as e:
            logger.error(f"Erro ao extrair texto da imagem: {str(e)}")
            return None

    def processar_diretorio(self, diretorio: str) -> List[Dict[str, Any]]:
        """
        Processa todos os arquivos PDF em um diretório.

        Args:
            diretorio: Caminho para o diretório contendo arquivos PDF

        Returns:
            Lista de dicionários com os dados extraídos de cada arquivo
        """
        logger.info(f"Processando diretório: {diretorio}")

        # Verificar se o diretório existe
        if not os.path.exists(diretorio):
            logger.error(f"Diretório não encontrado: {diretorio}")
            raise FileNotFoundError(f"Diretório não encontrado: {diretorio}")

        # Listar todos os arquivos PDF no diretório
        arquivos_pdf = [os.path.join(diretorio, arquivo) for arquivo in os.listdir(diretorio)
                        if arquivo.lower().endswith('.pdf')]

        if not arquivos_pdf:
            logger.warning(
                f"Nenhum arquivo PDF encontrado no diretório: {diretorio}")
            return []

        # Processar cada arquivo PDF
        resultados = []
        for arquivo_pdf in arquivos_pdf:
            try:
                resultado = self.processar_arquivo(arquivo_pdf)
                resultados.append(resultado)
            except Exception as e:
                logger.error(
                    f"Erro ao processar o arquivo {arquivo_pdf}: {str(e)}")
                continue

        return resultados


def main():
    """
    Função principal para execução do script.
    """
    parser = argparse.ArgumentParser(
        description='Extrator de Dados Técnicos de Catálogos (Versão Ajustada)')
    parser.add_argument('--api-key', type=str,
                        help='Chave de API do Mistral', required=True)
    parser.add_argument('--arquivo', type=str,
                        help='Caminho para o arquivo PDF a ser processado')
    parser.add_argument('--diretorio', type=str,
                        help='Caminho para o diretório contendo arquivos PDF')

    args = parser.parse_args()

    if not args.arquivo and not args.diretorio:
        parser.error("É necessário fornecer --arquivo ou --diretorio")

    extrator = ExtratorDadosTecnicos(api_key=args.api_key)

    if args.arquivo:
        extrator.processar_arquivo(args.arquivo)
    elif args.diretorio:
        extrator.processar_diretorio(args.diretorio)


if __name__ == "__main__":
    main()
