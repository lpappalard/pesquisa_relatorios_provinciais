import re
import os
import csv
from pypdf import PdfReader

# ========= Funções de contexto histórico ========= #

def periodo_historico(ano):
    if ano == "" or ano is None:
        return ""
    ano = int(ano)
    if 1840 <= ano <= 1888:
        return "Império – Segundo Reinado"
    elif 1889 <= ano <= 1894:
        return "República da Espada"
    elif 1895 <= ano <= 1930:
        return "República Velha"
    elif 1930 <= ano <= 1945:
        return "Era Vargas"
    else:
        return ""

PRESIDENTES = {
    1889: "Deodoro da Fonseca",
    1891: "Floriano Peixoto",
    1894: "Prudente de Morais",
    1898: "Campos Sales",
    1902: "Rodrigues Alves",
    1906: "Afonso Pena",
    1909: "Nilo Peçanha",
    1910: "Hermes da Fonseca",
    1914: "Venceslau Brás",
    1918: "Delfim Moreira",
    1919: "Epitácio Pessoa",
    1922: "Artur Bernardes",
    1926: "Washington Luís",
    1930: "Getúlio Vargas"
}

def presidente_federal(ano):
    if ano == "" or ano is None:
        return ""
    ano = int(ano)
    escolhido = ""
    for inicio, nome in sorted(PRESIDENTES.items()):
        if ano >= inicio:
            escolhido = nome
    return escolhido

# Governantes de São Paulo (pode expandir depois)
GOVERNANTES_SP = {
    1898: "Fernando Prestes",
    1904: "Jorge Tibiriçá",
    1911: "Manoel Joaquim Albuquerque Lins",
    1916: "Altino Arantes",
    1920: "Washington Luís",
    1924: "Carlos de Campos",
    1927: "Júlio Prestes",
}

def governante_sp(ano):
    if ano == "" or ano is None:
        return ""
    ano = int(ano)
    escolhido = ""
    for inicio, nome in sorted(GOVERNANTES_SP.items()):
        if ano >= inicio:
            escolhido = nome
    return escolhido

# ========= Lugares e localização ========= #

LUGARES = [
    "Iguape", "Pariquera", "Pariquera-Açu", "Registro", "Eldorado",
    "Juquiá", "Xiririca", "Itapetininga",
    "Serra do Paranapanema", "Vale do Ribeira"
]

def extrair_local(texto):
    encontrados = [l for l in LUGARES if l.lower() in texto.lower()]
    return "; ".join(encontrados)

# ========= Palavras-chave por categoria ========= #

CATEGORIAS = {
    "clima_insalubridade": [
        "insalubr", "miasma", "febre", "palud", "clima", "umidade",
    ],
    "vazio_matas_classificacao": [
        "mattas", "matas", "sertão", "sertao", "deserto", "inculto", "despovoado"
    ],
    "progresso_aproveitamento": [
        "aproveit", "civiliza", "progresso", "aprimor"
    ],
    "racismo_trabalho": [
        "vadio", "improdut", "ocioso", "indolente"
    ],
    "estradas_caminhos": [
        "estrada", "caminho", "viação", "viacao", "ponte"
    ],
    "ferrovias": [
        "ferrovi", "ferro-carril", "estrada de ferro"
    ],
    "geodesia_limites": [
        "triangula", "geodes", "marco", "limite", "divisa", "mediç", "medic"
    ],
    "meteorologia": [
        "estação meteor", "estacao meteor", "pluviomet", "baromet", "observatorio"
    ],
    "devolutas_regularizacao": [
        "devolut", "regulariza", "posse", "sesmaria", "titul"
    ],
    "colonizacao_imigracao": [
        "imigra", "colono", "colonia", "coloniza"
    ],
    "indigenas_quilombolas": [
        "indio", "indígen", "indigen", "aldeamento", "aldeia",
        "catequese", "quilomb", "caboclo"
    ]
}

# ========= CONFIG ========= #

PASTA = "relatorios_ocr"      # pasta onde estão os PDFs já com OCR
SAIDA = "planilha_relatorios.csv"

# se quiser gerar link direto pro CRL com base no número do arquivo
LINK_BASE = "https://digitalcollections.crl.edu/record/"

# ========= Funções auxiliares ========= #

def extrair_texto(pdf):
    """Lê as primeiras páginas do PDF e retorna texto em minúsculas."""
    try:
        reader = PdfReader(pdf)
    except Exception as e:
        print("  !! erro ao abrir PDF:", e)
        return ""
    texto = ""
    # você pode aumentar para 10 páginas se quiser
    for p in reader.pages[:5]:
        try:
            texto += p.extract_text() or ""
        except Exception as e:
            print("  !! erro extraindo texto de uma página:", e)
    return texto.lower()


def achar_ano(texto):
    # inclui 1850–1930 explícito
    anos = re.findall(r"(18[5-9]\d|19[0-2]\d|1930)", texto)
    return int(anos[0]) if anos else ""


def achar_mes(texto):
    meses = [
        "janeiro","fevereiro","março","marco","abril","maio","junho",
        "julho","agosto","setembro","outubro","novembro","dezembro"
    ]
    for m in meses:
        if m in texto:
            return m
    return ""


def achar_titulo(texto):
    linhas = texto.split("\n")
    for l in linhas[:15]:
        if "relatorio" in l or "relatório" in l:
            return l.strip().title()
    return ""


def buscar_citacoes(texto):
    resultados = []
    for cat, termos in CATEGORIAS.items():
        for t in termos:
            pos = texto.find(t)
            if pos != -1:
                trecho = texto[max(0, pos-80): pos+160]
                resultados.append((cat, t, trecho.strip()))
    return resultados


# ========= Processamento principal ========= #

linhas = []

for nome in sorted(os.listdir(PASTA)):
    if not nome.lower().endswith(".pdf"):
        continue

    caminho = os.path.join(PASTA, nome)
    print(">> analisando:", nome)

    texto = extrair_texto(caminho)

    ano = achar_ano(texto)
    mes = achar_mes(texto)
    titulo = achar_titulo(texto)
    periodo = periodo_historico(ano)
    presidente = presidente_federal(ano)
    governante = governante_sp(ano)
    localizacao = extrair_local(texto)

    link = ""
    if LINK_BASE and nome.split(".")[0].isdigit():
        # supõe que o nome do PDF é o número do record (ex: 5117.pdf)
        link = LINK_BASE + nome.split(".")[0]

    citacoes = buscar_citacoes(texto)

    # nenhum termo encontrado → ainda entra como linha "em branco"
    if not citacoes:
        linhas.append([
            "",           # ID
            link,
            nome,
            titulo,
            ano,
            mes,
            periodo,
            presidente,
            governante,
            "",           # Vice
            "",           # citacao
            "",           # categoria_analítica
            "",           # tema
            "",           # p_chave
            "",           # politica_associada
            "",           # consequencia_territorial
            localizacao,  # localizacao_mencionada
            "",           # nivel_evidencia
            ""            # observação interpretativa
        ])
        continue

    # para cada ocorrência relevante, gera uma linha
    for cat, termo, trecho in citacoes:
        linhas.append([
            "",           # ID
            link,
            nome,
            titulo,
            ano,
            mes,
            periodo,
            presidente,
            governante,
            "",           # Vice (você preenche depois se quiser)
            trecho,
            cat,
            cat.replace("_", " "),
            termo,
            "",           # politica_associada (manual/depois)
            "",           # consequencia_territorial (manual/depois)
            localizacao,
            "automática",
            "pré-selecionado por palavra-chave"
        ])

# ========= salvar CSV ========= #

with open(SAIDA, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow([
        "ID","link","nome_arq","titulo","ano","mês","periodo",
        "presidente","governante","Vice","citacao","categoria_analítica",
        "tema","p_chave","politica_associada","consequencia_territorial",
        "localizacao_mencionada","nivel_evidencia","observação interpretativa"
    ])
    w.writerows(linhas)

print("\n✔ Planilha criada:", SAIDA)
