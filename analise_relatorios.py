import pandas as pd

df = pd.read_csv("planilha_relatorios.csv", delimiter=";")

# 👉 cria a coluna década
df["decada"] = (df["ano"] // 10) * 10
por_decada = df.groupby("decada").size()

print(por_decada)

tabela = pd.crosstab(df["decada"], df["categoria_analítica"])
print(tabela)

print(df[["ano", "decada"]].head())
print(df.shape)
