import pandas as pd

# anos que você quer cobrir
anos = list(range(1850, 1931))

# ---------- PRESIDENTES DO BRASIL (simples, 1 nome por ano) ---------- #
presidentes = {}

# Império
for a in range(1850, 1889):
    presidentes[a] = "Dom Pedro II"

# República Velha e 1930 (esquema simplificado por ano)
presidentes.update({
    1889: "Deodoro da Fonseca",
    1890: "Deodoro da Fonseca",
    1891: "Deodoro da Fonseca",
    1892: "Floriano Peixoto",
    1893: "Floriano Peixoto",
    1894: "Prudente de Morais",
    1895: "Prudente de Morais",
    1896: "Prudente de Morais",
    1897: "Prudente de Morais",
    1898: "Campos Sales",
    1899: "Campos Sales",
    1900: "Campos Sales",
    1901: "Campos Sales",
    1902: "Rodrigues Alves",
    1903: "Rodrigues Alves",
    1904: "Rodrigues Alves",
    1905: "Rodrigues Alves",
    1906: "Afonso Pena",
    1907: "Afonso Pena",
    1908: "Afonso Pena",
    1909: "Nilo Peçanha",
    1910: "Hermes da Fonseca",
    1911: "Hermes da Fonseca",
    1912: "Hermes da Fonseca",
    1913: "Hermes da Fonseca",
    1914: "Venceslau Brás",
    1915: "Venceslau Brás",
    1916: "Venceslau Brás",
    1917: "Venceslau Brás",
    1918: "Venceslau Brás",       # simplificado
    1919: "Epitácio Pessoa",      # simplificado
    1920: "Epitácio Pessoa",
    1921: "Epitácio Pessoa",
    1922: "Artur Bernardes",
    1923: "Artur Bernardes",
    1924: "Artur Bernardes",
    1925: "Artur Bernardes",
    1926: "Washington Luís",
    1927: "Washington Luís",
    1928: "Washington Luís",
    1929: "Washington Luís",
    1930: "Getúlio Vargas",
})

# ---------- GOVERNANTES DE SP ---------- #
# Aqui vamos deixar em branco pra você completar/editAR manualmente depois
# (dá menos dor de cabeça do que tentar codar tudo agora)

dados = []

for ano in anos:
    dados.append({
        "ano": ano,
        "presidente_brasil": presidentes.get(ano, ""),
        "governante_sp": ""   # você preenche depois no CSV
    })

df = pd.DataFrame(dados)

# salva o CSV na mesma pasta
df.to_csv("chave_governo_1850_1930.csv", index=False)

print("✔ Planilha criada: chave_governo_1850_1930.csv")
