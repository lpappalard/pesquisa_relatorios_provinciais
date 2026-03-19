import os
import csv
from pypdf import PdfReader

PASTA = "/Users/laurapappalardo/Library/Mobile Documents/com~apple~CloudDocs/_doutorado/arquivo/CGG/relatorios_agricultura/_raspagem_RAGRIC/pdf_ocr"

OUT = "base_paginas_agricultura.csv"

def extrair(pdf):
    try:
        r = PdfReader(pdf)
        return [p.extract_text() or "" for p in r.pages]
    except:
        return []

linhas = []

for nome in sorted(os.listdir(PASTA)):
    if not nome.endswith(".pdf"):
        continue

    caminho = os.path.join(PASTA, nome)
    print("->", nome)

    paginas = extrair(caminho)

    for i, txt in enumerate(paginas, start=1):
        linhas.append([nome, i, txt.lower(), "agricultura"])

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["arquivo","pagina","texto","fonte"])
    w.writerows(linhas)

print("✔ base criada:", OUT)
