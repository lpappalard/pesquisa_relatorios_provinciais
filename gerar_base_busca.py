import os
import csv
import unicodedata
from pypdf import PdfReader
import re

PASTA = "relatorios_ocr"   # a mesma pasta dos PDFs
CSV_PAGINAS = "base_paginas_busca.csv"

def sem_acento(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", str(s))
        if unicodedata.category(c) != "Mn"
    )

def extrair_texto(pdf):
    try:
        reader = PdfReader(pdf)
    except Exception:
        return []
    paginas = []
    for p in reader.pages:
        try:
            tx = p.extract_text() or ""
        except Exception:
            tx = ""
        paginas.append(tx)
    return paginas

def achar_ano(txt):
    anos = re.findall(r"(18[5-9]\d|19[0-2]\d|1930)", txt)
    return int(anos[0]) if anos else ""

def main():
    linhas = []

    for nome in sorted(os.listdir(PASTA)):
        if not nome.lower().endswith(".pdf"):
            continue

        caminho = os.path.join(PASTA, nome)
        print(">> lendo:", nome)

        paginas = extrair_texto(caminho)
        if not paginas:
            continue

        texto_total = " ".join(paginas).lower()
        ano = achar_ano(texto_total)

        for idx, texto in enumerate(paginas, start=1):
            # guarda texto original e uma versão minúscula sem acento
            texto_norm = sem_acento(texto.lower())
            linhas.append([
                nome,
                ano,
                idx,
                texto_norm
            ])

    with open(CSV_PAGINAS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["arquivo", "ano", "pagina", "texto_norm"])
        w.writerows(linhas)

    print("✔ Base de busca criada:", CSV_PAGINAS)

if __name__ == "__main__":
    main()
