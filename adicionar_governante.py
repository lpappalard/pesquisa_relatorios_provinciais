import pandas as pd

# === mesmo mapeamento que você já usa ===
GOV_SP = {
    1842:"Antonio da Costa Pinto",
    1844:"José da Costa Carvalho",
    1848:"Bernardo Gavião Peixoto",
    1850:"Vicente Pires da Motta",
    1853:"José Thomaz Nabuco de Araújo",
    1857:"Jerônimo José Teixeira Júnior",
    1860:"Antônio Roberto de Almeida",
    1872:"Sebastião José Pereira",
    1886:"Prudente de Morais",

    # República – Governadores
    1898:"Fernando Prestes",
    1904:"Jorge Tibiriçá",
    1911:"Manoel Joaquim Albuquerque Lins",
    1916:"Altino Arantes",
    1920:"Washington Luís",
    1924:"Carlos de Campos",
    1927:"Júlio Prestes",
}

def governante_sp(ano):
    if pd.isna(ano):
        return ""
    try:
        ano = int(ano)
    except:
        return ""
    escolhido = ""
    for inicio, nome in sorted(GOV_SP.items()):
        if ano >= inicio:
            escolhido = nome
    return escolhido


# ---- carregar base unificada ----
df = pd.read_csv("base_busca_unificada.csv")

# se não tiver coluna ano, me avise!
df["governante"] = df["ano"].apply(governante_sp)

df.to_csv("base_busca_unificada.csv", index=False)

print("✔ governante adicionado à base unificada")
