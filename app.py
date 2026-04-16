import streamlit as st
import pandas as pd
import folium
from folium.plugins import FeatureGroupSubGroup
from streamlit_folium import st_folium

# 1. Configuração da página do Streamlit
st.set_page_config(page_title="Mapa de Endereços", layout="wide")
st.title("Mapa de Endereços Recorrentes")

# 2. Carregar os dados do CSV
@st.cache_data
def carregar_dados():
    # Substitua pelo nome exato do seu arquivo se tiver alterado
    df = pd.read_csv("Enderecos_recorrentes.xlsx - Sheet1.csv")
    return df

df = carregar_dados()

# 3. Criar o Mapa Base
# Centralizando o mapa na média das latitudes e longitudes dos seus dados
lat_media = df['Latitude'].mean()
lon_media = df['Longitude'].mean()

m = folium.Map(location=[lat_media, lon_media], zoom_start=15, control_scale=True)

# 4. Adicionar as Camadas Base (Basemaps)
# OpenStreetMap (Padrão - bom para ver nomes de ruas)
folium.TileLayer('OpenStreetMap', name='OpenStreetMap (Ruas)').add_to(m)

# Esri Satellite
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Esri Satélite',
    overlay=False,
    control=True
).add_to(m)

# Esri Traditional (Streets)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Esri Maps Tradicional',
    overlay=False,
    control=True
).add_to(m)

# 5. Organizar a "Legenda" (Controlando por Bairro ou Tabela)
# Vamos criar grupos com base na coluna "Bairro" para servir como legenda separada
bairros = df['Bairro'].unique()

for bairro in bairros:
    # Cria um grupo no controle de camadas para cada bairro
    grupo_bairro = folium.FeatureGroup(name=f"Bairro: {bairro}")
    
    # Filtra os dados apenas para o bairro atual
    df_bairro = df[df['Bairro'] == bairro]
    
    for idx, row in df_bairro.iterrows():
        # Criação do texto GRANDE para exibir permanentemente ao lado do ponto
        texto_html = f'''
            <div style="
                font-size: 14pt; 
                font-weight: bold; 
                color: #A00; 
                background-color: rgba(255,255,255,0.8); 
                padding: 4px; 
                border: 1px solid black;
                border-radius: 5px; 
                white-space: nowrap;">
                {row['Rua']}
            </div>
        '''
        
        # Adiciona o pino tradicional com informações no popup
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row['Localizaçāo'],
            tooltip="Clique para ver os detalhes",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(grupo_bairro)
        
        # Adiciona a "Label" gigante ao lado do pino
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            icon=folium.features.DivIcon(
                icon_size=(150,36),
                icon_anchor=(-15, -15), # Afasta o texto do pino para não sobrepor
                html=texto_html
            )
        ).add_to(grupo_bairro)
        
    # Adiciona o grupo do bairro ao mapa
    grupo_bairro.add_to(m)

# 6. Adicionar o Controlador de Camadas (Layer Control)
# É isso que permite ligar/desligar mapas e ligar/desligar os pontos pela legenda
folium.LayerControl(collapsed=False).add_to(m)

# 7. Renderizar o mapa dentro do Streamlit
st_folium(m, width="100%", height=700)
