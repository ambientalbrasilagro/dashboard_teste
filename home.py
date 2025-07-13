import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static, st_folium
from car_downloader import baixar_car
from zona_utm import calcular_utm

# Para rodar
# Ctrl J
# streamlit run c:/Users/elizabeth.sanchez/Desktop/mba_dash/home.py

# streamlit - Framework de desenvolvimento de dashboards interativos mantido pelo Google
# plotly - Biblioteca de plotagem de gráficos
# folium - Biblioteca de confecção de mapas
# Streamlit_folium - biblioteca de integração do streamlit com o folium


# Funções de disposição de elementos na tela
st.title('Dashboard Brasilagro em Python')
st.subheader('')
st.sidebar.title('Menu')

# Upload de um arquivo
arquivo_upload = st.sidebar.file_uploader('Selecione o arquivo a ser analisado')

# Upload de um CAR
car_escolhido = st.sidebar.text_input(label='Digite o código do CAR')

# para rodar na nuvem
embargo = '/dados/embargos/adm_embargos_ibama_a.shp'
desmatamento = '/dados/prodes/yearly_deforestation-2002-2024.shp'
tis = '/dados/ti/ti_sirgasPolygon.shp'
# para rodar no local
#embargo = r'dados\embargos\adm_embargos_ibama_a.shp'
#desmatamento = r'dados\prodes\yearly_deforestation-2002-2024.shp'
#tis = r'dados\ti\ti_sirgasPolygon.shp'

compacto = st.sidebar.checkbox(label='Dashboard')

if car_escolhido and not compacto:
        # Elemento de selação da visualização
        elemento=st.sidebar.radio('Selecione o elemento a ser visualizado',options=['Mapa','Gráfico','Resumo','Cabeçalho'])
        car_download = baixar_car(car_escolhido)
        # checagem para saber se um arquivo foi subido
        if car_escolhido:
                # Leitura do arquivo na forma de um geodataframe
                gdf = car_download

                @st.cache_resource
                def abrir_embargo():
                        gdf_embargo = gpd.read_file(embargo)
                        return gdf_embargo
                
                @st.cache_resource
                def abrir_desmatamento():
                        gdf_desmat = gpd.read_file(desmatamento)
                        return gdf_desmat
                
                @st.cache_resource
                def abrir_tis():
                        gdf_ti = gpd.read_file(tis)
                        return gdf_ti
                
                gdf_embargo = abrir_embargo()
                gdf_desmat = abrir_desmatamento()
                gdf_ti = abrir_tis()

                int_embargo = gpd.sjoin(gdf_embargo,gdf, how='inner', predicate='intersects')
                int_embargo = gpd.overlay(int_embargo,gdf,how='intersection')
                
                int_desmat = gpd.sjoin(gdf_desmat,gdf, how='inner', predicate='intersects')
                int_desmat = gpd.overlay(int_desmat,gdf,how='intersection')
                
                int_ti = gpd.sjoin(gdf_ti,gdf, how='inner', predicate='intersects')
                int_ti = gpd.overlay(int_ti,gdf,how='intersection')

                # Conversão de geodataframe para dataframe
                df_embargo = pd.DataFrame(int_embargo).drop(columns=['geometry'])
                df_desmat = pd.DataFrame(int_desmat).drop(columns=['geometry'])
                df_ti = pd.DataFrame(int_ti).drop(columns=['geometry'])
                
                # Criar funções para separar os elementos
                def resumo():
                        # Divisão em colunas para melhor visualização
                        col1, col2 = st.columns(2)

                        with col1:
                                st.dataframe(df_embargo, height=350)
                                st.dataframe(df_desmat, height=350)
                                st.dataframe(df_ti, height=350)
                        with col2:
                                st.dataframe(df_embargo.describe(),height=350)
                                st.dataframe(df_desmat.describe(),height=350)
                                st.dataframe(df_ti.describe(),height=350)

                def cabecalho():             
                        #st.dataframe(df)
                        st.subheader('Dados de embargo')
                        st.dataframe(df_embargo)
                        st.subheader('Dados de desmatamento')
                        st.dataframe(df_desmat)
                        st.subheader('Dados de terras indígenas')
                        st.dataframe(df_ti)

                def grafico():
                        col1_gra, col2_gra, col3_gra, col4_gra = st.columns(4)
                        
                        # Seleção do tema do gráfico
                        tema_gra = col1_gra.selectbox('Selecione o tema do gráfico',options=['Embargo','Desmatamento','Terras indígenas'])
                        
                        if tema_gra == 'Embargo':
                                df_analisado = df_embargo
                        elif tema_gra == 'Desmatamento':
                                df_analisado = df_desmat
                        elif tema_gra == 'Terras indígenas':
                                df_analisado = df_ti

                        # Seleção do tipo de gráfico e definição de seleção padrão (index)
                        tipo_gra = col2_gra.selectbox('Selecione o tipo de gráfico',options=['box','bar','line','scatter','violin','histogram'],index=1)
                
                        # Plotagem da função utilizando o plotly express
                        plot_func = getattr(px, tipo_gra)
                        
                        # Criação de opções dos eixos x e y com uma opção padrão (vai depender da tabela de atributos do arquivo)
                        x_val = col3_gra.selectbox('Selecione o eixo x',options=df_analisado.columns,index=1)
                        y_val = col4_gra.selectbox('Selecione o eixo y',options=df_analisado.columns,index=2)

                        # Crio a plotagem do gráfico
                        plot = plot_func(df_analisado, x=x_val,y=y_val)
                        # Faço a plotagem
                        st.plotly_chart(plot, use_container_width=True)

                def mapa():
                        global gdf, int_embargo, int_desmat, int_ti
                        st.subheader('Mapa interativo')
                        # Crio o mapa e seleciono opções
                        m = folium.Map(location=[-14,-54], zoom_start=4, control_scale=True, tiles='Esri World Imagery')
                        # Variável p/ receber o gdf
                                        
                        # Converte todas as colunas (exceto geometry) para string, caso necessário
                        def converter_colunas_datetime(gdf_entrada):
                                for col in gdf_entrada.columns:
                                        if col != 'geometry' and pd.api.types.is_datetime64_any_dtype(gdf_entrada[col]):
                                                gdf_entrada[col] = gdf_entrada[col].astype(str)
                                return gdf_entrada

                        # Converte datas para string em todos os GeoDataFrames antes da plotagem
                        gdf = converter_colunas_datetime(gdf)
                        int_embargo = converter_colunas_datetime(int_embargo)
                        int_desmat = converter_colunas_datetime(int_desmat)
                        int_ti = converter_colunas_datetime(int_ti)


                        def style_function_gdf(x): return{
                                'color': 'red',
                                'weight': 1.5,
                                'fillOpacity': 0
                        }
                        def style_function_embargo(x): return{
                                'fillColor': 'orange',
                                'color': 'black',
                                'weight': 0.5,
                                'fillOpacity': .50
                        }
                        def style_function_desmat(x): return{
                                'fillColor': 'purple',
                                'color': 'black',
                                'weight': 0.5,
                                'fillOpacity': .50
                        }
                        def style_function_ti(x): return{
                                'fillColor': 'yellow',
                                'color': 'black',
                                'weight': 0.5,
                                'fillOpacity': .50
                        }
                        # Plotagem do geodataframe no mapa
                        folium.GeoJson(int_embargo,style_function=style_function_embargo).add_to(m)
                        folium.GeoJson(int_desmat,style_function=style_function_desmat).add_to(m)
                        folium.GeoJson(int_ti,style_function=style_function_ti).add_to(m)
                        folium.GeoJson(gdf,style_function=style_function_gdf).add_to(m)

                        # Cálculo dos limites da geometria
                        bounds = gdf.total_bounds
                        # Definição da área de visualização do mapa
                        m.fit_bounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]])
                        # Adiciona controle de camadas no mapa
                        folium.LayerControl().add_to(m)
                        # Plotagem do mapa no daqshboard
                        st_folium(m,width="100%")

                # Condicional para mostrar os elementos da tela
                if elemento == 'Cabeçalho':
                        cabecalho()
                elif elemento == 'Resumo':
                        resumo()
                elif elemento == 'Gráfico':
                        grafico()
                else:
                        mapa()
 
        else:
                st.warning('Selecione um arquivo para iniciar a análise')

elif car_escolhido and compacto:
        car_download = baixar_car(car_escolhido)
        epsg = calcular_utm(car_download)
        # Leitura do arquivo na forma de um geodataframe
        gdf = car_download

        @st.cache_resource
        def abrir_embargo():
                gdf_embargo = gpd.read_file(embargo)
                return gdf_embargo
        
        @st.cache_resource
        def abrir_desmatamento():
                gdf_desmat = gpd.read_file(desmatamento)
                return gdf_desmat
        
        @st.cache_resource
        def abrir_tis():
                gdf_ti = gpd.read_file(tis)
                return gdf_ti
        
        gdf_embargo = abrir_embargo()
        gdf_desmat = abrir_desmatamento()
        gdf_ti = abrir_tis()

        # método para recortar apenas as áreas que intersectam com a feição
        int_embargo = gpd.sjoin(gdf_embargo,gdf, how='inner', predicate='intersects')
        int_embargo = gpd.overlay(int_embargo,gdf,how='intersection')
        
        int_desmat = gpd.sjoin(gdf_desmat,gdf, how='inner', predicate='intersects')
        int_desmat = gpd.overlay(int_desmat,gdf,how='intersection')
        
        int_ti = gpd.sjoin(gdf_ti,gdf, how='inner', predicate='intersects')
        int_ti = gpd.overlay(int_ti,gdf,how='intersection')

        # Conversão de geodataframe para dataframe
        df_embargo = pd.DataFrame(int_embargo).drop(columns=['geometry'])
        df_desmat = pd.DataFrame(int_desmat).drop(columns=['geometry'])
        df_ti = pd.DataFrame(int_ti).drop(columns=['geometry'])

        # cálculo de áreas dos cards

        area_desmat = int_desmat.dissolve(by=None)
        area_desmat = area_desmat.to_crs(epsg=epsg)
        area_desmat['area'] = area_desmat.area/10000
        
        area_embargo = int_embargo.dissolve(by=None)
        area_embargo = area_embargo.to_crs(epsg=epsg)
        area_embargo['area'] = area_embargo.area/10000
        
        area_ti = int_ti.dissolve(by=None)
        area_ti = area_ti.to_crs(epsg=epsg)
        area_ti['area'] = area_ti.area/10000

        #st.markdown("<h3 style='text-align: center;'>Dashboard CAR</h3>", unsafe_allow_html=True)

        #CARDS
        card_column1, card_column2, card_column3 = st.columns(3)

        with card_column1:
                st.write('Área total desmatada')
                if len(area_desmat)==0:
                        st.subheader('0 ha')
                else:
                        st.subheader(str(round(area_desmat.loc[0,'area'],2)))
        with card_column2:
                st.write('Área total de embargos')
                if len(area_embargo)==0:
                        st.subheader('0 ha')
                else:
                        st.subheader(str(round(area_embargo.loc[0,'area'],2)))
        with card_column3:
                st.write('Área total de terras indígenas')
                if len(area_ti)==0:
                        st.subheader('0 ha')
                else:
                        st.subheader(str(round(area_ti.loc[0,'area'],2)))
        
        #GRÁFICO
        col1_gra, col2_gra, col3_gra, col4_gra = st.columns(4)
                        
        # Seleção do tema do gráfico
        tema_gra = col1_gra.selectbox('Selecione o tema do gráfico',options=['Embargo','Desmatamento','Terras indígenas'])
        
        if tema_gra == 'Embargo':
                df_analisado = df_embargo
        elif tema_gra == 'Desmatamento':
                df_analisado = df_desmat
        elif tema_gra == 'Terras indígenas':
                df_analisado = df_ti

        # Seleção do tipo de gráfico e definição de seleção padrão (index)
        tipo_gra = col2_gra.selectbox('Selecione o tipo de gráfico',options=['box','bar','line','scatter','violin','histogram'],index=1)

        # Plotagem da função utilizando o plotly express
        plot_func = getattr(px, tipo_gra)
        
        # Criação de opções dos eixos x e y com uma opção padrão (vai depender da tabela de atributos do arquivo)
        x_val = col3_gra.selectbox('Selecione o eixo x',options=df_analisado.columns,index=1)
        y_val = col4_gra.selectbox('Selecione o eixo y',options=df_analisado.columns,index=2)

        # Crio a plotagem do gráfico
        plot = plot_func(df_analisado, x=x_val,y=y_val)
        # Faço a plotagem
        st.plotly_chart(plot, use_container_width=True)

        #MAPA
        st.subheader('Mapa interativo')
        # Crio o mapa e seleciono opções
        m = folium.Map(zoom_start=4, control_scale=True, tiles='Esri World Imagery')
        # Variável p/ receber o gdf
                        
        # Converte todas as colunas (exceto geometry) para string, caso necessário
        def converter_colunas_datetime(gdf_entrada):
                for col in gdf_entrada.columns:
                        if col != 'geometry' and pd.api.types.is_datetime64_any_dtype(gdf_entrada[col]):
                                gdf_entrada[col] = gdf_entrada[col].astype(str)
                return gdf_entrada

        # Converte datas para string em todos os GeoDataFrames antes da plotagem
        gdf = converter_colunas_datetime(gdf)
        int_embargo = converter_colunas_datetime(int_embargo)
        int_desmat = converter_colunas_datetime(int_desmat)
        int_ti = converter_colunas_datetime(int_ti)


        def style_function_gdf(x): return{
                'color': 'red',
                'weight': 1.5,
                'fillOpacity': 0
        }
        def style_function_embargo(x): return{
                'fillColor': 'orange',
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': .50
        }
        def style_function_desmat(x): return{
                'fillColor': 'purple',
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': .50
        }
        def style_function_ti(x): return{
                'fillColor': 'yellow',
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': .50
        }
        # Plotagem do geodataframe no mapa
        folium.GeoJson(int_embargo,style_function=style_function_embargo).add_to(m)
        folium.GeoJson(int_desmat,style_function=style_function_desmat).add_to(m)
        folium.GeoJson(int_ti,style_function=style_function_ti).add_to(m)
        folium.GeoJson(gdf,style_function=style_function_gdf).add_to(m)

        # Cálculo dos limites da geometria
        bounds = gdf.total_bounds
        # Definição da área de visualização do mapa
        m.fit_bounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]])
        # Adiciona controle de camadas no mapa
        folium.LayerControl().add_to(m)
        # Plotagem do mapa no daqshboard
        st_folium(m,width="100%")

elif arquivo_upload and not compacto:
        # Elemento de selação da visualização
        elemento=st.sidebar.radio('Selecione o elemento a ser visualizado',options=['Mapa','Gráfico','Resumo','Cabeçalho'])
        # Leitura do arquivo na forma de um geodataframe
        gdf = gpd.read_file(arquivo_upload)

        @st.cache_resource
        def abrir_embargo():
                gdf_embargo = gpd.read_file(embargo)
                return gdf_embargo
        
        @st.cache_resource
        def abrir_desmatamento():
                gdf_desmat = gpd.read_file(desmatamento)
                return gdf_desmat
        
        @st.cache_resource
        def abrir_tis():
                gdf_ti = gpd.read_file(tis)
                return gdf_ti
        
        gdf_embargo = abrir_embargo()
        gdf_desmat = abrir_desmatamento()
        gdf_ti = abrir_tis()

        int_embargo = gpd.sjoin(gdf_embargo,gdf, how='inner', predicate='intersects')
        int_embargo = gpd.overlay(int_embargo,gdf,how='intersection')
        
        int_desmat = gpd.sjoin(gdf_desmat,gdf, how='inner', predicate='intersects')
        int_desmat = gpd.overlay(int_desmat,gdf,how='intersection')
        
        int_ti = gpd.sjoin(gdf_ti,gdf, how='inner', predicate='intersects')
        int_ti = gpd.overlay(int_ti,gdf,how='intersection')

        # Conversão de geodataframe para dataframe
        df_embargo = pd.DataFrame(int_embargo).drop(columns=['geometry'])
        df_desmat = pd.DataFrame(int_desmat).drop(columns=['geometry'])
        df_ti = pd.DataFrame(int_ti).drop(columns=['geometry'])
        
        # Criar funções para separar os elementos
        def resumo():
                # Divisão em colunas para melhor visualização
                col1, col2 = st.columns(2)

                with col1:
                        st.dataframe(df_embargo, height=350)
                        st.dataframe(df_desmat, height=350)
                        st.dataframe(df_ti, height=350)
                with col2:
                        st.dataframe(df_embargo.describe(),height=350)
                        st.dataframe(df_desmat.describe(),height=350)
                        st.dataframe(df_ti.describe(),height=350)

        def cabecalho():             
                #st.dataframe(df)
                st.subheader('Dados de embargo')
                st.dataframe(df_embargo)
                st.subheader('Dados de desmatamento')
                st.dataframe(df_desmat)
                st.subheader('Dados de terras indígenas')
                st.dataframe(df_ti)

        def grafico():
                col1_gra, col2_gra, col3_gra, col4_gra = st.columns(4)
                
                # Seleção do tema do gráfico
                tema_gra = col1_gra.selectbox('Selecione o tema do gráfico',options=['Embargo','Desmatamento','Terras indígenas'])
                
                if tema_gra == 'Embargo':
                        df_analisado = df_embargo
                elif tema_gra == 'Desmatamento':
                        df_analisado = df_desmat
                elif tema_gra == 'Terras indígenas':
                        df_analisado = df_ti

                # Seleção do tipo de gráfico e definição de seleção padrão (index)
                tipo_gra = col2_gra.selectbox('Selecione o tipo de gráfico',options=['box','bar','line','scatter','violin','histogram'],index=1)
               
                # Plotagem da função utilizando o plotly express
                plot_func = getattr(px, tipo_gra)
                
                # Criação de opções dos eixos x e y com uma opção padrão (vai depender da tabela de atributos do arquivo)
                x_val = col3_gra.selectbox('Selecione o eixo x',options=df_analisado.columns,index=1)
                y_val = col4_gra.selectbox('Selecione o eixo y',options=df_analisado.columns,index=2)

                # Crio a plotagem do gráfico
                plot = plot_func(df_analisado, x=x_val,y=y_val)
                # Faço a plotagem
                st.plotly_chart(plot, use_container_width=True)

        def mapa():
                global gdf, int_embargo, int_desmat, int_ti
                st.subheader('Mapa interativo')
                # Crio o mapa e seleciono opções
                m = folium.Map(location=[-14,-54], zoom_start=4, control_scale=True, tiles='Esri World Imagery')
                # Variável p/ receber o gdf
                                
                # Converte todas as colunas (exceto geometry) para string, caso necessário
                def converter_colunas_datetime(gdf_entrada):
                        for col in gdf_entrada.columns:
                                if col != 'geometry' and pd.api.types.is_datetime64_any_dtype(gdf_entrada[col]):
                                        gdf_entrada[col] = gdf_entrada[col].astype(str)
                        return gdf_entrada

                # Converte datas para string em todos os GeoDataFrames antes da plotagem
                gdf = converter_colunas_datetime(gdf)
                int_embargo = converter_colunas_datetime(int_embargo)
                int_desmat = converter_colunas_datetime(int_desmat)
                int_ti = converter_colunas_datetime(int_ti)


                def style_function_gdf(x): return{
                        'color': 'red',
                        'weight': 1.5,
                        'fillOpacity': 0
                }
                def style_function_embargo(x): return{
                        'fillColor': 'orange',
                        'color': 'black',
                        'weight': 0.5,
                        'fillOpacity': .50
                }
                def style_function_desmat(x): return{
                        'fillColor': 'purple',
                        'color': 'black',
                        'weight': 0.5,
                        'fillOpacity': .50
                }
                def style_function_ti(x): return{
                        'fillColor': 'yellow',
                        'color': 'black',
                        'weight': 0.5,
                        'fillOpacity': .50
                }
                # Plotagem do geodataframe no mapa
                folium.GeoJson(int_embargo,style_function=style_function_embargo).add_to(m)
                folium.GeoJson(int_desmat,style_function=style_function_desmat).add_to(m)
                folium.GeoJson(int_ti,style_function=style_function_ti).add_to(m)
                folium.GeoJson(gdf,style_function=style_function_gdf).add_to(m)

                # Cálculo dos limites da geometria
                bounds = gdf.total_bounds
                # Definição da área de visualização do mapa
                m.fit_bounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]])
                # Adiciona controle de camadas no mapa
                folium.LayerControl().add_to(m)
                # Plotagem do mapa no daqshboard
                st_folium(m,width="100%")

        # Condicional para mostrar os elementos da tela
        if elemento == 'Cabeçalho':
                cabecalho()
        elif elemento == 'Resumo':
                resumo()
        elif elemento == 'Gráfico':
                grafico()
        else:
                mapa()

elif arquivo_upload and compacto:
        gdf = gpd.read_file(arquivo_upload)
        epsg = calcular_utm(gdf)
        # Leitura do arquivo na forma de um geodataframe

        @st.cache_resource
        def abrir_embargo():
                gdf_embargo = gpd.read_file(embargo)
                return gdf_embargo
        
        @st.cache_resource
        def abrir_desmatamento():
                gdf_desmat = gpd.read_file(desmatamento)
                return gdf_desmat
        
        @st.cache_resource
        def abrir_tis():
                gdf_ti = gpd.read_file(tis)
                return gdf_ti
        
        gdf_embargo = abrir_embargo()
        gdf_desmat = abrir_desmatamento()
        gdf_ti = abrir_tis()

        # método para recortar apenas as áreas que intersectam com a feição
        int_embargo = gpd.sjoin(gdf_embargo,gdf, how='inner', predicate='intersects')
        int_embargo = gpd.overlay(int_embargo,gdf,how='intersection')
        
        int_desmat = gpd.sjoin(gdf_desmat,gdf, how='inner', predicate='intersects')
        int_desmat = gpd.overlay(int_desmat,gdf,how='intersection')
        
        int_ti = gpd.sjoin(gdf_ti,gdf, how='inner', predicate='intersects')
        int_ti = gpd.overlay(int_ti,gdf,how='intersection')

        # Conversão de geodataframe para dataframe
        df_embargo = pd.DataFrame(int_embargo).drop(columns=['geometry'])
        df_desmat = pd.DataFrame(int_desmat).drop(columns=['geometry'])
        df_ti = pd.DataFrame(int_ti).drop(columns=['geometry'])

        # cálculo de áreas dos cards

        area_desmat = int_desmat.dissolve(by=None)
        area_desmat = area_desmat.to_crs(epsg=epsg)
        area_desmat['area'] = area_desmat.area/10000
        
        area_embargo = int_embargo.dissolve(by=None)
        area_embargo = area_embargo.to_crs(epsg=epsg)
        area_embargo['area'] = area_embargo.area/10000
        
        area_ti = int_ti.dissolve(by=None)
        area_ti = area_ti.to_crs(epsg=epsg)
        area_ti['area'] = area_ti.area/10000

        #st.markdown("<h3 style='text-align: center;'>Dashboard CAR</h3>", unsafe_allow_html=True)

        #CARDS
        card_column1, card_column2, card_column3 = st.columns(3)

        with card_column1:
                st.write('Área total desmatada')
                if len(area_desmat)==0:
                        st.subheader('0 ha')
                else:
                        st.subheader(str(round(area_desmat.loc[0,'area'],2)))
        with card_column2:
                st.write('Área total de embargos')
                if len(area_embargo)==0:
                        st.subheader('0 ha')
                else:
                        st.subheader(str(round(area_embargo.loc[0,'area'],2)))
        with card_column3:
                st.write('Área total de terras indígenas')
                if len(area_ti)==0:
                        st.subheader('0 ha')
                else:
                        st.subheader(str(round(area_ti.loc[0,'area'],2)))
        
        #GRÁFICO
        col1_gra, col2_gra, col3_gra, col4_gra = st.columns(4)
                        
        # Seleção do tema do gráfico
        tema_gra = col1_gra.selectbox('Selecione o tema do gráfico',options=['Embargo','Desmatamento','Terras indígenas'])
        
        if tema_gra == 'Embargo':
                df_analisado = df_embargo
        elif tema_gra == 'Desmatamento':
                df_analisado = df_desmat
        elif tema_gra == 'Terras indígenas':
                df_analisado = df_ti

        # Seleção do tipo de gráfico e definição de seleção padrão (index)
        tipo_gra = col2_gra.selectbox('Selecione o tipo de gráfico',options=['box','bar','line','scatter','violin','histogram'],index=1)

        # Plotagem da função utilizando o plotly express
        plot_func = getattr(px, tipo_gra)
        
        # Criação de opções dos eixos x e y com uma opção padrão (vai depender da tabela de atributos do arquivo)
        x_val = col3_gra.selectbox('Selecione o eixo x',options=df_analisado.columns,index=1)
        y_val = col4_gra.selectbox('Selecione o eixo y',options=df_analisado.columns,index=2)

        # Crio a plotagem do gráfico
        plot = plot_func(df_analisado, x=x_val,y=y_val)
        # Faço a plotagem
        st.plotly_chart(plot, use_container_width=True)

        #MAPA
        st.subheader('Mapa interativo')
        # Crio o mapa e seleciono opções
        m = folium.Map(zoom_start=4, control_scale=True, tiles='Esri World Imagery')
        # Variável p/ receber o gdf
                        
        # Converte todas as colunas (exceto geometry) para string, caso necessário
        def converter_colunas_datetime(gdf_entrada):
                for col in gdf_entrada.columns:
                        if col != 'geometry' and pd.api.types.is_datetime64_any_dtype(gdf_entrada[col]):
                                gdf_entrada[col] = gdf_entrada[col].astype(str)
                return gdf_entrada

        # Converte datas para string em todos os GeoDataFrames antes da plotagem
        gdf = converter_colunas_datetime(gdf)
        int_embargo = converter_colunas_datetime(int_embargo)
        int_desmat = converter_colunas_datetime(int_desmat)
        int_ti = converter_colunas_datetime(int_ti)


        def style_function_gdf(x): return{
                'color': 'red',
                'weight': 1.5,
                'fillOpacity': 0
        }
        def style_function_embargo(x): return{
                'fillColor': 'orange',
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': .50
        }
        def style_function_desmat(x): return{
                'fillColor': 'purple',
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': .50
        }
        def style_function_ti(x): return{
                'fillColor': 'yellow',
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': .50
        }
        # Plotagem do geodataframe no mapa
        folium.GeoJson(int_embargo,style_function=style_function_embargo).add_to(m)
        folium.GeoJson(int_desmat,style_function=style_function_desmat).add_to(m)
        folium.GeoJson(int_ti,style_function=style_function_ti).add_to(m)
        folium.GeoJson(gdf,style_function=style_function_gdf).add_to(m)

        # Cálculo dos limites da geometria
        bounds = gdf.total_bounds
        # Definição da área de visualização do mapa
        m.fit_bounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]])
        # Adiciona controle de camadas no mapa
        folium.LayerControl().add_to(m)
        # Plotagem do mapa no daqshboard
        st_folium(m,width="100%")       
else:
        st.warning('Selecione um arquivo ou digite um CAR para iniciar a análise')