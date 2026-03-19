import pandas as pd

prov = pd.read_csv("base_paginas_busca.csv", sep=";")
agri = pd.read_csv("base_paginas_agricultura.csv")

prov["colecao"] = "provincial"
agri["colecao"] = "agricultura"

base = pd.concat([prov, agri], ignore_index=True)

base = base.sort_values(["ano", "colecao", "arquivo", "pagina"], na_position="last")

base.to_csv("base_busca_unificada.csv", index=False)

print("✔ base unificada salva: base_busca_unificada.csv")
