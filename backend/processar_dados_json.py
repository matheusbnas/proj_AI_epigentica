import json
import re
import pandas as pd
from io import StringIO

def extrair_tabelas(texto):
    tabelas = []
    padrao_tabela = r"((?:\|.*\|\n)+)"
    for match in re.finditer(padrao_tabela, texto):
        tabela_md = match.group(1)
        try:
            # Remove linhas separadoras do markdown (ex: |---|---|)
            linhas = [l for l in tabela_md.strip().splitlines() if not re.match(r"^\s*\|?\s*-+\s*\|", l)]
            if len(linhas) < 2:
                continue
            tabela_str = "\n".join(linhas)
            df = pd.read_csv(StringIO(tabela_str), sep="|", engine="python", skipinitialspace=True)
            df = df.dropna(axis=1, how='all')
            cabecalho = [c.strip() for c in df.columns if c.strip()]
            linhas = df.values.tolist()
            tabelas.append({"cabecalho": cabecalho, "linhas": linhas})
        except Exception:
            continue
    return tabelas

def limpar_texto(texto):
    # Remove tabelas markdown
    texto = re.sub(r"((?:\|.*\|\n)+)", "", texto)
    # Remove marcações markdown
    texto = re.sub(r"#+\s*", "", texto)
    texto = re.sub(r"\$\$?.*?\$\$?", "", texto)  # Remove LaTeX simples
    texto = texto.replace("**", "").replace("*", "")
    return texto.strip()

def extrair_titulo(texto):
    linhas = texto.splitlines()
    for linha in linhas:
        if linha.strip().startswith("#"):
            return linha.strip("# ").strip()
    return ""

def processar_json(input_path, output_path):
    with open(input_path, encoding="utf-8") as f:
        dados = json.load(f)
    novas_paginas = []
    for pagina in dados["paginas"]:
        texto = pagina.get("texto", "")
        tabelas = extrair_tabelas(texto)
        titulo = extrair_titulo(texto)
        texto_limpo = limpar_texto(texto)
        novas_paginas.append({
            "numero": pagina.get("numero"),
            "titulo": titulo,
            "texto": texto_limpo,
            "tabelas": tabelas,
            "imagens": pagina.get("imagens", [])
        })
    dados["paginas"] = novas_paginas
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def carregar_json_estruturado(path):
    """Carrega o arquivo JSON estruturado e retorna como dict."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# Exemplo de uso:
# processar_json("output/dados.json", "output/dados_estruturado.json")
