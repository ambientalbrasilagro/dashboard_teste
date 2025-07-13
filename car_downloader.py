import requests
import geopandas as gpd
from io import BytesIO
# pip install requests geopandas
# pip install streamlit plotly-express folium streamlit-folium

def baixar_car(cod_imovel):
    state = cod_imovel[0:2].lower()

    url = 'https://geoserver.car.gov.br/geoserver/sicar/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=sicar:sicar_imoveis_'+state+'&outputFormat=application/json&cql_filter=cod_imovel='+'\''+cod_imovel+'\''
    print(url)

    r = requests.get(url, allow_redirects=True, verify=False)

    gdf = gpd.read_file(BytesIO(r.content))

    return gdf

if __name__ == '__main__':
    baixar_car('BA-2917359-773CA6D5CD1F49CB9FD5E19EDBA9105A')