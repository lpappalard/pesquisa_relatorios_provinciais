import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

plt.style.use("seaborn-v0_8")


def grafico_categoria(rel, categoria, titulo=None):

    # não descarta governadores/presidentes nulos (anos antigos!)
    base = (
        rel[rel["categoria_analítica"] == categoria]
        .groupby(["ano", "presidente", "governante"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values("ano")
    )

    if base.empty:
        print(f"[!] Sem dados para {categoria}")
        return

    dados = base

    fig, ax = plt.subplots(figsize=(13, 6))

    # linha principal
    ax.plot(dados["ano"], dados["n"], marker="o", linewidth=2)

    # título alinhado esquerda
    fig.suptitle(
        titulo or categoria.replace("_"," ").title(),
        fontsize=15, weight="bold",
        x=0.02, y=0.97, ha="left"
    )

    ax.set_xlabel("Ano")
    ax.set_ylabel("Ocorrências")
    ax.grid(alpha=0.25)

    # escala de tempo completa
    ax.set_xlim(1850, int(rel["ano"].max()))
    # --- mostrar TODOS os anos no eixo ---
    anos = list(range(1850, int(rel["ano"].max()) + 1))
    ax.set_xticks(anos)

    # rótulos pequenos e discretos
    ax.tick_params(axis="x", labelsize=7, rotation=90, pad=2)

    ax.xaxis.set_major_locator(MultipleLocator(5))

    ymax = dados["n"].max()
    ax.set_ylim(0, ymax * 1.75)

    # --------------------
    # GOVERNADORES (azul)
    # --------------------
    ultimo_gov = None
    for _, row in dados.iterrows():
        gov = row["governante"]

        if gov != ultimo_gov:
            ax.axvline(row["ano"], linestyle="--", alpha=0.35, color="steelblue")
            ax.text(
                row["ano"], ymax * 1.80,
                gov if isinstance(gov, str) else "",
                rotation=28, fontsize=7,
                ha="left", va="bottom",
                color="steelblue"
            )
            ultimo_gov = gov

    # --------------------
    # PRESIDENTES (vermelho — linha até o nome)
    # --------------------
    ultimo_pres = None
    for _, row in dados.iterrows():
        pres = row["presidente"] if pd.notna(row["presidente"]) else "—"

        if pres != ultimo_pres:

            y_label = ymax * 2.20   # posição do nome

            # linha sobe até o texto
            ax.plot(
                [row["ano"], row["ano"]],
                [0, y_label],
                linestyle=":", color="darkred", alpha=0.45
            )

            ax.text(
                row["ano"], y_label,
                pres,
                rotation=28,
                fontsize=6,
                ha="left", va="bottom",
                color="darkred"
            )

            ultimo_pres = pres

    # --------------------
    # PICOS (top 3)
    # --------------------
    top_picos = dados.sort_values("n", ascending=False).head(3)

    for _, row in top_picos.iterrows():
        ax.scatter(row["ano"], row["n"] + ymax*0.03, s=90, color="black", zorder=5)

        ax.text(
            row["ano"], row["n"] + ymax*0.14,
            f"{int(row['ano'])}\nPres.: {row['presidente']}\nGov.: {row['governante']}",
            fontsize=8, ha="left", va="bottom"
        )

    plt.tight_layout(rect=[0,0,1,0.82])

    nome = f"grafico_{categoria}.png"
    plt.savefig(nome, dpi=300, bbox_inches="tight")
    plt.show()

    print(f"✔ salvo: {nome}")

CATS = [
        "devolutas_regularizacao",
        "geodesia_limites",
        "estradas_caminhos",
        "colonizacao_imigracao",
        "clima_insalubridade",
        "indigenas_quilombolas",
        "meteorologia",
        "ferrovias",
]

def gerar_todos(rel):
    for c in CATS:
        print(f"\n=== {c} ===")
        grafico_categoria(rel, c, titulo=c.replace("_"," ").title())

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

def grafico_comparativo(rel):
    """
    Sobrepõe todas as categorias,
    destacando o pico de cada uma com ano + governante + presidente.
    """

    categorias = sorted(rel["categoria_analítica"].dropna().unique())

    fig, ax = plt.subplots(figsize=(15, 8))

    base = (
        rel.groupby(["ano", "categoria_analítica"])
        .size()
        .reset_index(name="n")
        .sort_values(["categoria_analítica", "ano"])
    )

    for cat in categorias:
        dados = base[base["categoria_analítica"] == cat]

        ax.plot(
            dados["ano"],
            dados["n"],
            linewidth=2,
            marker="o",
            alpha=0.8,
            label=cat.replace("_", " ").title()
        )

        # --- detectar pico ---
        pico = dados.loc[dados["n"].idxmax()]

        ano_pico = int(pico["ano"])
        valor = pico["n"]

        # recuperar governante/presidente daquele ano
        contexto = (
            rel[(rel["ano"] == ano_pico) &
                (rel["categoria_analítica"] == cat)]
            [["presidente", "governante"]]
            .mode()
        )

        pres = contexto["presidente"].iloc[0] if not contexto.empty else "—"
        gov  = contexto["governante"].iloc[0] if not contexto.empty else "—"

        # marcar o ponto
        ax.scatter(ano_pico, valor, s=90, color="black", zorder=5)

        # anotação (leve, fora do ponto)
        ax.text(
            ano_pico,
            valor + (base["n"].max() * 0.03),
            f"{ano_pico}\nPres.: {pres}\nGov.: {gov}",
            fontsize=8,
            ha="center",
            va="bottom"
        )

    # eixo X
    ax.set_xlim(1850, int(rel["ano"].max()))
    ax.xaxis.set_major_locator(MultipleLocator(5))

    ax.set_xlabel("Ano")
    ax.set_ylabel("Ocorrências")
    ax.grid(alpha=0.25)

    plt.title(
        "Comparativo — Picos por Categoria",
        fontsize=17,
        weight="bold",
        loc="left"
    )

    ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=9
    )

    plt.tight_layout()
    plt.savefig("grafico_comparativo.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("✔ salvo: grafico_comparativo.png")

import pandas as pd

def gerar_planilha_picos(rel):
    # 1) contagem por ano + categoria
    base = (
        rel.groupby(["ano", "categoria_analítica"], dropna=False)
           .size()
           .reset_index(name="n")
    )

    # 2) encontrar o ano do pico para cada categoria
    picos = (
        base.loc[base.groupby("categoria_analítica")["n"].idxmax()]
        .copy()
        .sort_values("ano")
    )

    # 3) juntar presidente e governante daquele ano
    info = (
        rel[["ano", "presidente", "governante"]]
        .drop_duplicates(subset=["ano"])
    )

    picos = picos.merge(info, on="ano", how="left")

    # 4) deixar bonitinho
    picos.rename(columns={
        "categoria_analítica": "categoria",
        "n": "ocorrencias",
        "ano": "ano_do_pico"
    }, inplace=True)

    # 5) exportar
    nome = "picos_por_categoria.xlsx"
    picos.to_excel(nome, index=False)

    print(f"✔ Planilha criada: {nome}")
    return picos
