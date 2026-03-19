import streamlit as st
import pandas as pd
from difflib import SequenceMatcher
import unicodedata
import altair as alt
import re
from collections import Counter

st.set_page_config(layout="wide")
st.markdown("## Buscar termos:\n- Relatórios Presidenciais da província de São Paulo (1850-1930)\n- Relatórios da Secretaria de Agricultura (1880-1930)")
st.markdown("[baixar relatorios](https://drive.google.com/drive/folders/1UhyRxnprxZtQylzZJ0DW6L6XWwpt9LCg?usp=sharing)")

STOPWORDS = set("""
de da do das dos a o os as que e em para por com se ao na no nos nas elle segundo alguns nesta
uma um umas uns este esta esse essa isso pelo pela entre sobre contra idem sera data 
onde quando como qual quais mais menos ja ainda nao ser foi sao tem deste desde cada 
lhe sua suas seu digital seu tambem muito pouco porem pois porque fazer quanto francisco 
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

def parecido(a, b):
    return SequenceMatcher(None, a, b).ratio()

def normalizar(s):
    s = str(s).lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

@st.cache_data
def carregar_base():
    df = pd.read_csv(
        "base_busca_unificada_com_governo.csv",
        engine="python",
        on_bad_lines="skip"
    )

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    else:
        df["ano"] = None

    possiveis_colunas = ["texto_norm", "texto", "texto_original", "conteudo"]

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

    if "colecao" not in df.columns:
        df["colecao"] = "desconhecida"

    if "governante_sp" not in df.columns:
        df["governante_sp"] = ""

    if "presidente_brasil" not in df.columns:
        df["presidente_brasil"] = ""

    return df

with st.spinner("Carregando base (CSV) e normalizando texto..."):
    df = carregar_base()

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

# sempre trabalhamos a partir de uma cópia
df_filtrado = df.copy()

# ---- tipo de relatório ----
# força índice zero para não manter valor antigo em session state
tipo_relatorio = st.sidebar.radio(
    "Tipo de relatório:",
    ["Todos", "Provincial/Presidencial", "Agricultura"],
    index=0,
)

# nota: escolha "Todos" para pesquisar em todos os relatórios, caso contrário
# apenas a coleção selecionada será usada (ex.: Agricultura).

if tipo_relatorio == "Provincial/Presidencial":
    df_filtrado = df_filtrado[df_filtrado["colecao"] != "agricultura"]
elif tipo_relatorio == "Agricultura":
    df_filtrado = df_filtrado[df_filtrado["colecao"] == "agricultura"]

# ---- coleção ----
colecoes = sorted(df_filtrado["colecao"].dropna().unique())

colecao_sel = st.sidebar.multiselect(
    "Coleções:",
    options=colecoes,
    default=colecoes,
    key="colecao_sel"
)

# se o usuário voltar para "Todos", ignorar seleção anterior e usar todas as coleções
if tipo_relatorio == "Todos":
    colecao_sel = colecoes

# aplica o filtro final de coleções
if colecao_sel:
    df_filtrado = df_filtrado[df_filtrado["colecao"].isin(colecao_sel)]
else:
    # nenhum colecao selecionada -> resulta vazio
    df_filtrado = df_filtrado.iloc[0:0]

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
consulta = st.text_input("Termos (aspas para frases contínuas, vírgula para separar)", "")

# Permite consultas como: "indigena guarani", arroz, "caminho de ferro"
termos = []
for token in re.findall(r'"([^"]+)"|\'([^\']+)\'|[^,]+', consulta):
    # token é uma tupla por causa dos grupos alternados
    termo = next((t for t in token if t), "").strip()
    if termo:
        termos.append(termo.lower())

usar_aprox = st.checkbox("Incluir busca aproximada (OCR)", value=False)

resultados_mult = {}
for termo in termos:
    mask = df_filtro["texto_norm"].str.contains(re.escape(termo), na=False)
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
    anos_completos = list(range(1850, 1931))
    for termo in termos:
        df_term = resultados_mult[termo]
        if df_term.empty:
            # criar série vazia preenchida em todas as datas
            serie_termo = pd.DataFrame({
                "ano": anos_completos,
                "ocorrencias": [0] * len(anos_completos)
            })
        else:
            serie_termo = (
                df_term
                .groupby("ano")
                .size()
                .reset_index(name="ocorrencias")
            )
            # garantir todos os anos para evitar linha quebrada
            serie_termo = (
                serie_termo
                .set_index("ano")
                .reindex(anos_completos, fill_value=0)
                .reset_index()
            )
        serie_termo["termo"] = termo
        grafs.append(serie_termo)

    # preparar dados preenchendo qualquer ano faltante entre 1850 e 1930
    anos_completos = list(range(1850, 1931))
    if grafs:
        listas = []
        for df_termo in grafs:
            termo = df_termo.loc[0, "termo"]
            df_full = (
                df_termo
                .set_index("ano")
                .reindex(anos_completos, fill_value=0)
                .reset_index()
            )
            # após o reindex, pode sobrar coluna termo; manter apenas ano e ocorrencias
            if "termo" in df_full.columns:
                df_full = df_full[["ano", "ocorrencias"]]
            df_full["termo"] = termo
            listas.append(df_full)
        dados = pd.concat(listas, ignore_index=True)
    else:
        dados = pd.DataFrame()

    st.subheader("Comparativo por termo")
    if not dados.empty:
        st.altair_chart(
            alt.Chart(dados)
            .mark_line(point=True)
            .encode(
                x=alt.X("ano:O", scale=alt.Scale(domain=anos_completos)),
                y="ocorrencias:Q",
                color="termo:N",
                tooltip=["ano", "termo", "ocorrencias"]
            ),
            width="stretch"
        )
    else:
        st.info("Sem dados para o comparativo por termo com os filtros atuais.")

    # gráfico por governante e ano para os termos pesquisados
    gov_term_list = []
    for termo, df_term in resultados_mult.items():
        if df_term.empty:
            continue
        gcounts = (
            df_term
            .dropna(subset=["governante_sp", "ano"])
            .groupby(["governante_sp", "ano"])
            .size()
            .reset_index(name="ocorrencias")
        )
        gcounts["termo"] = termo
        gov_term_list.append(gcounts)

    if gov_term_list:
        gov_anos = pd.concat(gov_term_list, ignore_index=True)
    else:
        gov_anos = pd.DataFrame()

    st.subheader("Ocorrências por governante e ano")
    if not gov_anos.empty:
        chart_gov = (
            alt.Chart(gov_anos)
            .mark_bar()
            .encode(
                x="ano:O",
                y="ocorrencias:Q",
                color="governante_sp:N",
                column="termo:N",
                tooltip=["governante_sp", "ano", "ocorrencias", "termo"]
            )
        )
        st.altair_chart(chart_gov, width="stretch")
    else:
        # tenta ao menos mostrar contagem por governante sem considerar ano
        tot_gov = (
            df_para_graficos
            .dropna(subset=["governante_sp"])
            .groupby("governante_sp")
            .size()
            .reset_index(name="ocorrencias")
        )
        if not tot_gov.empty:
            st.info("Nenhum registro com ano disponível para os termos. exibindo contagem por governante apenas.")
            chart_simple = (
                alt.Chart(tot_gov)
                .mark_bar()
                .encode(
                    x="ocorrencias:Q",
                    y=alt.Y("governante_sp:N", sort='-x'),
                    tooltip=["governante_sp", "ocorrencias"]
                )
            )
            st.altair_chart(chart_simple, width="stretch")
        else:
            st.info("Sem dados de governantes para os termos pesquisados.")

    # gráfico simples de total por governante (independente de ano)
    tot_gov = (
        df_para_graficos
        .dropna(subset=["governante_sp"])
        .groupby("governante_sp")
        .size()
        .reset_index(name="ocorrencias")
    )
    if not tot_gov.empty:
        st.subheader("Total de ocorrências por governante")
        chart_tot = (
            alt.Chart(tot_gov)
            .mark_bar()
            .encode(
                x="ocorrencias:Q",
                y=alt.Y("governante_sp:N", sort='-x'),
                tooltip=["governante_sp", "ocorrencias"]
            )
        )
        st.altair_chart(chart_tot, width="stretch")

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

# ---------- PICOS ---------- #
st.subheader("Picos detectados")

if not serie.empty:
    picos = (
        serie.sort_values("ocorrencias", ascending=False)
        .groupby("colecao")
        .head(3)
    )
    st.dataframe(picos, width="stretch")

st.subheader("-----------------------------------")

st.subheader("Pico 100 palavras")

if st.button("Calcular pico 100"):
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

st.subheader("Pico de palavras por década")

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


st.subheader("Palavras mais frequentes")

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

st.subheader("Pico de palavras por governante")

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

st.subheader("Pico de palavras por década")

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
