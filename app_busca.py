import streamlit as st
import pandas as pd
from difflib import SequenceMatcher
import unicodedata
import altair as alt
import re
from collections import Counter

STOPWORDS = set("""
de da do das dos a o os as que e em para por com se ao na no nos nas elle segundo alguns nesta
uma um umas uns este esta esse essa isso pelo pela entre sobre contra idem sera data 
onde quando como qual quais mais menos ja ainda nao ser foi sao tem deste desde cada 
lhe sua suas seus digital seu tambem muito pouco porem pois porque fazer quanto francisco 
nao foi tem ser sua aos ate ao sem art nio seus todos desta tendo annos outros
assim sido dia mas bem sao todas suas quaes alem vos lhe pelos grande maior mesma 
con ella mez eee pois pro paulo sendo mesmo foram durante anno jose antonio geral 
""".split())


def remover_acentos(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

def limpar_texto(t):
    t = remover_acentos(str(t).lower())
    palavras = re.findall(r"\b[a-z]+\b", t)
    return [p for p in palavras if p not in STOPWORDS and len(p) > 3]

def contar_palavras(textos, n=100):
    todas = []
    for t in textos.dropna():
        todas.extend(limpar_texto(t))
    return Counter(todas).most_common(n)

# ---------- utilidades ---------- #

def parecido(a, b):
    return SequenceMatcher(None, a, b).ratio()

def normalizar(s):
    s = str(s).lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


# ---------- carregar base ---------- #
@st.cache_data
def carregar_base():
    df = pd.read_csv(
        "base_busca_unificada_com_governo.csv",
        engine="python",
        on_bad_lines="skip"
    )

    # ---- ano ----
    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    else:
        df["ano"] = None

    # ---- texto normalizado (sempre garantir preenchido) ----
    possiveis_colunas = ["texto_norm", "texto", "texto_original", "conteudo"]

    # (corrigido) monta uma Series de texto concatenando colunas existentes
    textos = []
    for col in possiveis_colunas:
        if col in df.columns:
            textos.append(df[col].fillna("").astype(str))

    if textos:
        base_texto = textos[0]
        for s in textos[1:]:
            base_texto = base_texto + " " + s
    else:
        base_texto = pd.Series([""] * len(df), index=df.index)

    df["texto_norm"] = base_texto.apply(normalizar)

    # ---- coleção ----
    if "colecao" not in df.columns:
        df["colecao"] = "desconhecida"

    # ---- governantes (novos) ----
    if "governante_sp" not in df.columns:
        df["governante_sp"] = ""

    if "presidente_brasil" not in df.columns:
        df["presidente_brasil"] = ""

    return df


# ---------- CARREGAR ---------- #
df = carregar_base()

# normaliza a coluna colecao para evitar erros
df["colecao"] = (
    df["colecao"]
      .astype(str)
      .str.strip()
      .str.lower()
)

# ---- governante (SP) ----
govs = ["(todos)"] + sorted(df["governante_sp"].dropna().unique())
gov_sel = st.sidebar.selectbox("Governante (SP):", govs)

if gov_sel != "(todos)":
    df = df[df["governante_sp"] == gov_sel]

# ---- presidente do Brasil ----
pres = ["(todos)"] + sorted(df["presidente_brasil"].dropna().unique())
pres_sel = st.sidebar.selectbox("Presidente do Brasil:", pres)

if pres_sel != "(todos)":
    df = df[df["presidente_brasil"] == pres_sel]


# ---------- UI ---------- #
st.title("Busca nos Relatórios Provinciais / Presidenciais e da Agricultura")
st.sidebar.header("Filtros")

# sempre trabalhamos a partir de uma cópia
df_filtrado = df.copy()

# ---- tipo de relatório ----
tipo_relatorio = st.sidebar.radio(
    "Tipo de relatório:",
    ["Todos", "Provincial/Presidencial", "Agricultura"]
)

if tipo_relatorio == "Provincial/Presidencial":
    df_filtrado = df_filtrado[df_filtrado["colecao"] != "agricultura"]
elif tipo_relatorio == "Agricultura":
    df_filtrado = df_filtrado[df_filtrado["colecao"] == "agricultura"]

# ---- coleção ----
colecoes = sorted(df_filtrado["colecao"].dropna().unique())

colecao_sel = st.sidebar.multiselect(
    "Coleções:",
    options=colecoes,
    default=colecoes
)

df_filtrado = df_filtrado[df_filtrado["colecao"].isin(colecao_sel)]

st.write("📦 Registros por coleção (após filtro):")
st.write(df_filtrado["colecao"].value_counts())

st.write("🔎 Linhas da AGRICULTURA sem texto_norm:")
st.write(df_filtrado[df_filtrado["colecao"] == "agricultura"]["texto_norm"].isna().sum())

# ---- anos ----
anos = sorted(df_filtrado["ano"].dropna().unique())
ano_min = int(min(anos)) if anos else 1850
ano_max = int(max(anos)) if anos else 1930

intervalo = st.sidebar.slider(
    "Ano:",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max)
)

df_filtro = df_filtrado[
    (df_filtrado["ano"] >= intervalo[0]) &
    (df_filtrado["ano"] <= intervalo[1])
].copy()

df_filtro["texto_norm"] = df_filtro["texto_norm"].fillna("").astype(str)


### <<< construir período (inicio–fim) por governante
if "governante_sp" in df.columns:

    periodos = (
        df.dropna(subset=["governante_sp", "ano"])
          .groupby("governante_sp")["ano"]
          .agg(inicio="min", fim="max")
          .reset_index()
    )

    periodos["rotulo_governante"] = periodos.apply(
        lambda r: f"{r['governante_sp']} ({int(r['inicio'])}-{int(r['fim'])})",
        axis=1
    )

    df = df.merge(
        periodos[["governante_sp", "rotulo_governante"]],
        on="governante_sp",
        how="left"
    )

### <<< seletor de governante
governantes_lista = ["(todos)"] + sorted(df["rotulo_governante"].dropna().unique())

gov_escolhido = st.selectbox(
    "Escolha o governante:",
    options=governantes_lista,
    index=0
)

# ---------- BUSCA ---------- #
consulta = st.text_input("Termos (separe por vírgula)", "")
termos = [t.strip().lower() for t in consulta.split(",") if t.strip()]

usar_aprox = st.checkbox("Incluir busca aproximada (OCR)", value=False)

resultados_mult = {}
for termo in termos:
    mask = df_filtro["texto_norm"].str.contains(termo, na=False)
    resultados_mult[termo] = df_filtro[mask].copy()

# ---------- RESULTADOS ---------- #
df_para_graficos = df_filtro.copy()

if termos:
    # concat seguro
    df_para_graficos = (
        pd.concat(resultados_mult.values(), ignore_index=True)
        .drop_duplicates()
    )

    st.write(f"**{len(df_para_graficos)} páginas** com pelo menos um termo.")

    # gráfico por termo
    grafs = []
    for termo in termos:
        if resultados_mult[termo].empty:
            continue
        serie_termo = (
            resultados_mult[termo]
            .groupby("ano")
            .size()
            .reset_index(name="ocorrencias")
        )
        serie_termo["termo"] = termo
        grafs.append(serie_termo)

    dados = pd.concat(grafs, ignore_index=True) if grafs else pd.DataFrame()

    st.subheader("Comparativo por termo")
    if not dados.empty:
        st.altair_chart(
            alt.Chart(dados)
            .mark_line(point=True)
            .encode(
                x="ano:O",
                y="ocorrencias:Q",
                color="termo:N",
                tooltip=["ano", "termo", "ocorrencias"]
            ),
            width="stretch"
        )
    else:
        st.info("Sem dados para o comparativo por termo com os filtros atuais.")

# ---------- TABELA ---------- #
if termos and not df_para_graficos.empty:
    st.subheader("Resultados")

    cols = [
        c for c in ["arquivo", "colecao", "ano", "pagina", "governante_sp", "presidente_brasil", "texto_norm"]
        if c in df_para_graficos.columns
    ]

    st.dataframe(df_para_graficos[cols], width="stretch")

    st.download_button(
        "Baixar CSV",
        data=df_para_graficos[cols].to_csv(index=False, sep=";"),
        file_name="resultados_busca.csv",
        mime="text/csv"
    )

# ---------- GRÁFICO POR COLEÇÃO ---------- #
st.subheader("Comparativo por coleção")

serie = pd.DataFrame()
if not df_para_graficos.empty:
    serie = (
        df_para_graficos
        .groupby(["ano", "colecao"])
        .size()
        .reset_index(name="ocorrencias")
    )

    if not serie.empty:
        st.altair_chart(
            alt.Chart(serie)
            .mark_line(point=True)
            .encode(
                x="ano:O",
                y="ocorrencias:Q",
                color="colecao:N"
            ),
            width="stretch"
        )
    else:
        st.info("Sem dados para o comparativo por coleção com os filtros atuais.")

# ---------- PICOS ---------- #
st.subheader("Picos detectados")

if not serie.empty:
    picos = (
        serie.sort_values("ocorrencias", ascending=False)
        .groupby("colecao")
        .head(3)
    )
    st.dataframe(picos, width="stretch")

# ---------- CORRELAÇÃO ---------- #
st.subheader("Correlação entre coleções")

if not df_para_graficos.empty:
    cross = (
        df_para_graficos
        .groupby(["ano", "colecao"])
        .size()
        .unstack(fill_value=0)
    )
    st.line_chart(cross)

st.subheader("-----------------------------------")

st.subheader("Top 100 palavras")

if st.button("Calcular top 100"):
    top = contar_palavras(df_filtro["texto_norm"], n=100)
    freq_df = pd.DataFrame(top, columns=["palavra", "frequencia"])

    st.dataframe(freq_df, width="stretch")

    chart = (
        alt.Chart(freq_df)
        .mark_bar()
        .encode(
            x="frequencia:Q",
            y=alt.Y("palavra:N", sort='-x'),
            tooltip=["palavra", "frequencia"]
        )
    )

    st.altair_chart(chart, width="stretch")

st.subheader("📆 Top palavras por década")

if st.button("Gerar gráfico por década"):
    df_dec = df_filtro.dropna(subset=["ano"]).copy()
    df_dec["decada"] = (df_dec["ano"] // 10) * 10

    registros = []
    for dec, grupo in df_dec.groupby("decada"):
        top = contar_palavras(grupo["texto_norm"], n=10)
        for palavra, freq in top:
            registros.append({"decada": int(dec), "palavra": palavra, "freq": freq})

    tabela = pd.DataFrame(registros)

    st.dataframe(tabela, width="stretch")

    chart = (
        alt.Chart(tabela)
        .mark_bar()
        .encode(
            x="freq:Q",
            y=alt.Y("palavra:N", sort='-x'),
            color="decada:N",
            column="decada:N",
            tooltip=["decada", "palavra", "freq"]
        )
    )

    st.altair_chart(chart, width="stretch")

st.subheader("Palavras mais frequentes por década")

if st.button("Gerar ranking por década"):
    df_dec = df_filtro.dropna(subset=["ano"]).copy()
    df_dec["decada"] = (df_dec["ano"] // 10) * 10

    resultados = []
    for dec, bloco in df_dec.groupby("decada"):
        top_dec = contar_palavras(bloco["texto_norm"], n=20)
        for palavra, freq in top_dec:
            resultados.append({"decada": int(dec), "palavra": palavra, "frequencia": freq})

    tabela = pd.DataFrame(resultados).sort_values(["decada", "frequencia"], ascending=[True, False])
    st.dataframe(tabela, width="stretch")


st.subheader("Palavras mais frequentes (com stopwords removidas)")

stop = STOPWORDS

def limpar(t):
    t = str(t).lower()
    t = re.sub(r"[^a-zà-ú0-9 ]", " ", t)
    return t.split()

df_freq = df_para_graficos.copy()

if not df_freq.empty:
    df_freq["decada"] = (df_freq["ano"] // 10) * 10

    contagens = []
    for dec, grupo in df_freq.groupby("decada"):
        palavras = Counter()
        for texto in grupo["texto_norm"]:
            palavras.update(w for w in limpar(texto) if w not in stop and len(w) > 3)

        for palavra, freq in palavras.most_common(100):
            contagens.append({"decada": dec, "palavra": palavra, "freq": freq})

    freq_df = pd.DataFrame(contagens)

    st.dataframe(freq_df, width="stretch")

    st.bar_chart(
        freq_df.groupby("palavra")["freq"].sum().sort_values(ascending=False).head(20)
    )

st.subheader("📊 Top palavras por governante")

if not df_freq.empty:
    tops_gov = []

    df_clean = df.dropna(subset=["rotulo_governante"]).copy()

    for gov, grupo in df_clean.groupby("rotulo_governante"):
        if gov_escolhido != "(todos)" and gov != gov_escolhido:
            continue

        palavras = Counter()
        for texto in grupo["texto_norm"]:
            palavras.update(w for w in limpar(texto) if w not in STOPWORDS and len(w) > 3)

        for palavra, freq in palavras.most_common(15):
            tops_gov.append({"governante": gov, "palavra": palavra, "freq": freq})

    if tops_gov:
        tops_gov_df = pd.DataFrame(tops_gov)

        chart = (
            alt.Chart(tops_gov_df)
            .mark_bar()
            .encode(
                x="freq:Q",
                y=alt.Y("palavra:N", sort='-x'),
                color="governante:N",
                tooltip=["governante", "palavra", "freq"]
            )
        )

        st.altair_chart(chart, width="stretch")
    else:
        st.info("Nenhum governante encontrado para o filtro atual.")

st.subheader("📆 Top palavras por década")

if not df_freq.empty:
    dec_tops = []

    for dec, grupo in df_freq.groupby("decada"):
        palavras = Counter()
        for texto in grupo["texto_norm"]:
            palavras.update(w for w in limpar(texto) if w not in stop and len(w) > 3)

        for palavra, freq in palavras.most_common(15):
            dec_tops.append({"decada": int(dec), "palavra": palavra, "freq": freq})

    dec_df = pd.DataFrame(dec_tops)

    st.dataframe(dec_df, width="stretch")

    chart = (
        alt.Chart(dec_df)
        .mark_bar()
        .encode(
            x="freq:Q",
            y=alt.Y("palavra:N", sort='-x'),
            color="decada:N",
            tooltip=["decada", "palavra", "freq"]
        )
    )

    st.altair_chart(chart, width="stretch")
