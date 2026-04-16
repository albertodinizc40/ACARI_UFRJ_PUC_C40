import html
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium


st.set_page_config(page_title="Mapa de Endereços", layout="wide")

ARQUIVO_EXCEL = "Enderecos_recorrentes.xlsx"

st.title("Mapa de endereços recorrentes")
st.caption("Cada aba da planilha vira uma camada própria no mapa.")


@st.cache_data
def carregar_planilhas(caminho_arquivo):
    xls = pd.ExcelFile(caminho_arquivo)
    dados = {}

    for aba in xls.sheet_names:
        df = pd.read_excel(caminho_arquivo, sheet_name=aba)
        df.columns = [str(c).strip() for c in df.columns]

        colunas_obrigatorias = ["Latitude", "Longitude"]
        for col in colunas_obrigatorias:
            if col not in df.columns:
                raise ValueError(
                    f"A aba '{aba}' não tem a coluna obrigatória: {col}"
                )

        if "Rua" not in df.columns:
            df["Rua"] = aba
        if "CEP" not in df.columns:
            df["CEP"] = ""
        if "Bairro" not in df.columns:
            df["Bairro"] = ""
        if "Cidade" not in df.columns:
            df["Cidade"] = ""
        if "Localização" not in df.columns:
            df["Localização"] = ""

        df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
        df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
        df = df.dropna(subset=["Latitude", "Longitude"]).copy()

        dados[aba] = df

    return dados


def criar_legenda(cores_por_aba):
    itens = ""

    for aba, cor in cores_por_aba.items():
        itens += f"""
        <div style="display:flex; align-items:center; margin-bottom:8px;">
            <span style="
                display:inline-block;
                width:14px;
                height:14px;
                border-radius:50%;
                background:{cor};
                margin-right:8px;
            "></span>
            <span style="font-size:14px;">{html.escape(aba)}</span>
        </div>
        """

    legenda = f"""
    <div style="
        position: fixed;
        bottom: 40px;
        left: 40px;
        width: 220px;
        z-index: 9999;
        background: white;
        border: 2px solid #444;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    ">
        <div style="font-size:16px; font-weight:700; margin-bottom:10px;">
            Legenda por tabela
        </div>
        {itens}
    </div>
    """

    return legenda


def gerar_mapa(dados, abas_visiveis, tamanho_rotulo):
    todas_lat = []
    todas_lon = []

    for aba in abas_visiveis:
        todas_lat.extend(dados[aba]["Latitude"].tolist())
        todas_lon.extend(dados[aba]["Longitude"].tolist())

    centro = [
        sum(todas_lat) / len(todas_lat),
        sum(todas_lon) / len(todas_lon),
    ]

    m = folium.Map(
        location=centro,
        zoom_start=16,
        control_scale=True,
        tiles=None,
    )

    # Base 1: OpenStreetMap
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        overlay=False,
        control=True,
        show=True,
    ).add_to(m)

    # Base 2: mapa tradicional
    folium.TileLayer(
        tiles="CartoDB Voyager",
        name="Mapa tradicional",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # Base 3: Esri satélite
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri",
        name="Esri Satélite",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # Camada opcional de rótulos sobre o satélite
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Labels © Esri",
        name="Rótulos sobre satélite",
        overlay=True,
        control=True,
        show=False,
        opacity=0.9,
    ).add_to(m)

    paleta = [
        "#d7191c",
        "#2c7bb6",
        "#1a9641",
        "#fdae61",
        "#6a3d9a",
        "#008080",
        "#ff1493",
        "#8b4513",
        "#4b0082",
        "#696969",
    ]

    cores_por_aba = {}

    for i, aba in enumerate(abas_visiveis):
        cor = paleta[i % len(paleta)]
        cores_por_aba[aba] = cor

        grupo = folium.FeatureGroup(name=f"Tabela: {aba}", show=True)
        df = dados[aba]

        for _, row in df.iterrows():
            rua = str(row.get("Rua", "")).strip()
            cep = str(row.get("CEP", "")).strip()
            bairro = str(row.get("Bairro", "")).strip()
            cidade = str(row.get("Cidade", "")).strip()
            localizacao = str(row.get("Localização", "")).strip()
            lat = row["Latitude"]
            lon = row["Longitude"]

            popup_html = f"""
            <div style='font-size:14px;'>
                <div><b>Tabela:</b> {html.escape(aba)}</div>
                <div><b>Rua:</b> {html.escape(rua)}</div>
                <div><b>CEP:</b> {html.escape(cep)}</div>
                <div><b>Bairro:</b> {html.escape(bairro)}</div>
                <div><b>Cidade:</b> {html.escape(cidade)}</div>
                <div><b>Localização:</b> {html.escape(localizacao)}</div>
                <div><b>Latitude:</b> {lat}</div>
                <div><b>Longitude:</b> {lon}</div>
            </div>
            """

            folium.CircleMarker(
                location=[lat, lon],
                radius=7,
                color=cor,
                fill=True,
                fill_color=cor,
                fill_opacity=1,
                weight=2,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"{aba} | {rua}",
            ).add_to(grupo)

            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size: {tamanho_rotulo}px;
                        font-weight: 800;
                        color: {cor};
                        white-space: nowrap;
                        text-shadow:
                            -1px -1px 0 #ffffff,
                             1px -1px 0 #ffffff,
                            -1px  1px 0 #ffffff,
                             1px  1px 0 #ffffff,
                             0px  0px 4px #ffffff;
                        transform: translate(10px, -6px);
                    ">{html.escape(rua)}</div>
                    """
                ),
            ).add_to(grupo)

        grupo.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    min_lat = min(todas_lat)
    max_lat = max(todas_lat)
    min_lon = min(todas_lon)
    max_lon = max(todas_lon)

    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    legenda = criar_legenda(cores_por_aba)
    m.get_root().html.add_child(folium.Element(legenda))

    return m


try:
    dados = carregar_planilhas(ARQUIVO_EXCEL)
    abas = list(dados.keys())

    st.sidebar.title("Controles")

    abas_visiveis = st.sidebar.multiselect(
        "Tabelas visíveis",
        options=abas,
        default=abas,
    )

    tamanho_rotulo = st.sidebar.slider(
        "Tamanho do nome dos pontos",
        min_value=12,
        max_value=28,
        value=18,
        step=1,
    )

    if not abas_visiveis:
        st.warning("Selecione pelo menos uma tabela na barra lateral.")
    else:
        mapa = gerar_mapa(dados, abas_visiveis, tamanho_rotulo)
        st_folium(mapa, use_container_width=True, height=700)

        st.subheader("Prévia dos dados")
        for aba in abas_visiveis:
            st.markdown(f"### {aba}")
            st.dataframe(dados[aba], use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar o aplicativo: {e}")
