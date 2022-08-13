import pandas as pd
import numpy as np
import altair as alt
import geopandas as gpd
import streamlit as st

europe = alt.topo_feature("https://raw.githubusercontent.com/deldersveld/topojson/master/continents/europe.json",'continent_Europe_subunits')
ordinates = pd.read_csv("C:\\Users\\Jutta\\Downloads\\Bachelorarbeit\\1-s2.0-S0160412021004463-mmc1.csv")
st.set_page_config(page_title="The Ramsey Highlights", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child{
        width: 260px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child{
        width: 260px;
        margin-left: -500px;
    }

    """,
    unsafe_allow_html=True,
)

st.markdown(f'''
            <style>
                .reportview-container .sidebar-content {{
                    padding-top: {0}rem;
                }}
                .reportview-container .main .block-container {{
                    padding-top: {0}rem;
                    padding-right: {10}rem;
                    padding-left: {1}rem;
                    padding-bottom: {10}rem;
                }}
            </style>
            ''', unsafe_allow_html=True,
)


with st.sidebar:
    sample = st.radio(
        "Please select OTUs to visualize: ",
        ('relative abundance of OTUs', 'OTUs'))
    if sample == 'relative abundance of OTUs':
        RMOTUs = pd.read_csv("C:\\Users\\Jutta\\Downloads\\Bachelorarbeit\\1-s2.0-S0160412021004463-mmc4.csv")
        rmdatasets = pd.read_csv("C:\\Users\\Jutta\\Downloads\\Bachelorarbeit\\1-s2.0-S0160412021004463-mmc5.csv")
        selections = rmdatasets['Phylum'].unique()
    else:
        OTUs = pd.read_csv("C:\\Users\\Jutta\\Downloads\\Bachelorarbeit\\1-s2.0-S0160412021004463-mmc2.csv")
        datasets = pd.read_csv("C:\\Users\\Jutta\\Downloads\\Bachelorarbeit\\1-s2.0-S0160412021004463-mmc3.csv")
        selections = datasets['tax_2'].unique()

    selectbox_phylum = st.selectbox(
        "Please select the phylum:",
        options=selections
    )
    show = st.checkbox("Visualization by country")
    if show:
        countries = ordinates['Country'].unique()
        selectedcountry = st.selectbox(
            "Please select country:",
            options=countries
        )
        map_type = st.radio("Please select the map type:",('Proportional symbol map','Chloropleth Map'))






if sample == 'relative abundance of OTUs':
    selected_phylum = rmdatasets[rmdatasets['Phylum'] == selectbox_phylum]
    new = pd.merge(selected_phylum, RMOTUs, how="left", on=["Unnamed: 0"])
    new.drop(new.columns[0:selected_phylum.shape[1]], axis=1, inplace=True)
    new = new.T
    new['Relative abundance'] = new.apply(lambda x: x.sum(), axis=1)
    new = new.iloc[:, -1].to_frame()
    new["lake"] = new.index.values
    lname = 'Relative abundance:Q'
    name = 'Relative abundance'


else:
    copy = OTUs
    copy.set_index('Unnamed: 0', inplace=True)
    copy = copy.T
    selected_phylum = datasets[datasets['tax_2'] == selectbox_phylum]
    selected_phylum.set_index('ID', inplace=True)
    new = pd.concat([selected_phylum, copy], axis=1, join="inner")
    new.loc['Sequencing reads'] = new.iloc[0:len(new), :].sum(axis=0)
    new.drop(new.columns[0:selected_phylum.shape[1]], axis=1, inplace=True)
    new = new.iloc[-1:]
    new = new.T
    new["lake"] = new.index.values
    lname = 'Sequencing reads:Q'
    name = 'Sequencing reads'

po = ordinates
po.set_index('Unnamed: 0',inplace=True)
new = pd.concat([new,po],axis=1,join='inner')
hover= alt.selection(type='single', on='click',empty='all')

def lakemap(europe,lname):
    return alt.layer(
        alt.Chart(europe).mark_geoshape(
            fill='#ddd', stroke='#fff', strokeWidth=1
        ).encode(
        ),
        alt.Chart(new).mark_circle().add_selection(
            hover
        ).encode(
            latitude='latitude:Q',
            longitude='longitude:Q',
            tooltip=[alt.Tooltip('Name:N'), alt.Tooltip('Country:N'),
                     alt.Tooltip(lname, format=",.0")],
            size=alt.Size(lname, scale=alt.Scale(range=[10, 100])),
            color=alt.condition(hover, alt.Color('Country:N', scale=alt.Scale(scheme='tableau20')), alt.value('gray'),
                                opacity=0.5),
            opacity=alt.condition(hover, alt.value(0.8), alt.value(0.1))
        )
        ).project(
            type='mercator', scale=380, translate=[200, 540]
        ).properties(
            width=800,
            height=800
        ).configure_view(
            stroke=None
        )

lakes = lakemap(europe,lname)

def psmap(land,color,lname):
    click = alt.selection(type='single', on='click', empty='all')
    return alt.layer(
        alt.Chart(land).mark_geoshape(
            fill='white', stroke='gray', strokeWidth=1
        ).encode(
        ),
        alt.Chart(new).mark_circle().transform_filter(
            alt.FieldEqualPredicate(field='Country', equal=selectedcountry)
        ).add_selection(click).encode(
            latitude='latitude:Q',
            longitude='longitude:Q',
            tooltip=[alt.Tooltip('Name:N'), alt.Tooltip('Country:N'),
                     alt.Tooltip(lname, format=",.0")],
            size=alt.Size(lname, scale=alt.Scale(range=[30, 200]), legend=alt.Legend(columns=2)),
            color=alt.condition(click, alt.Color('Name:N', scale=alt.Scale(scheme=color),
                                                 legend=alt.Legend(columns=3, title="The name of lakes", tickCount=4)),
                                alt.value('dimgray')),
            opacity=alt.condition(click, alt.value(0.8), alt.value(0.1))
        )
    ).properties(
        width=400,
        height=400
    ).configure_view(
        stroke=None
    ).configure_legend(
        orient='bottom',
        labelLimit=115
    )

def cmap(land, tooltip,color,lookup,data,width,height,lname,name):
    return alt.layer(
        alt.Chart(land).mark_geoshape(
            fill='lightgray', stroke='white', strokeWidth=0.25
        ).encode(
        ),
        alt.Chart(land).mark_geoshape().encode(
            tooltip=[alt.Tooltip(lname), alt.Tooltip(tooltip)],
            color=alt.Color(lname, scale=alt.Scale(scheme=color))
        ).transform_lookup(
            lookup=lookup,
            from_=alt.LookupData(data=data, key='Region',
                                 fields=[name])
        )
    ).properties(
        width=width,
        height=height
    ).configure_view(
        stroke=None
    ).configure_legend(
        orient='bottom'
    )


if show:
    if selectedcountry == 'Austria':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/ginseng666/GeoJSON-TopoJSON-Austria/master/2021/simplified-99.9/laender_999_topo.json",
            'laender')
    elif selectedcountry == 'Germany':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/AliceWi/TopoJSON-Germany/master/germany.json",
            'states')
    elif selectedcountry == 'Italy':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/italy/italy-regions.json",
            'ITA_adm1')
    elif selectedcountry == 'Switzerland':
        land = alt.topo_feature("https://raw.githubusercontent.com/samateja/D3topoJson/master/switzerland.json",
                                'switzerland')
    elif selectedcountry == 'Norway':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/norway/norway-new-counties.json",
            'Fylker')
    elif selectedcountry == 'Sweden':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/sweden/sweden-counties.json",
            'SWE_adm1')
    elif selectedcountry == 'Poland':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/poland/poland-provinces.json",
            'POL_adm1')
    elif selectedcountry == 'Slovak':
        land = alt.topo_feature("https://raw.githubusercontent.com/mlajtos/slovakia-topojson/master/slovakia.json",
                                'kraje')
    elif selectedcountry == 'Hungary':
        land = alt.topo_feature("https://code.highcharts.com/mapdata/countries/hu/hu-all.topo.json",'default')
    elif selectedcountry == 'Romania':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/romania/romania-counties.json",
            'ROU_adm1')
    elif selectedcountry == 'Czech republic':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/czech-republic/czech-republic-regions.json",
            'CZE_adm1')
    elif selectedcountry == 'France':
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/AtelierCartographie/Khartis/master/public/data/map/FR-reg-2016/france.json",
            'poly')
    else:
        land = alt.topo_feature(
            "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/spain/spain-comunidad.json",
            'ESP_adm1')

    if map_type == 'Proportional symbol map':
        map = psmap(land, 'goldgreen', lname)
        map1 = psmap(land, 'purplered', lname)
        map2 = psmap(land, 'viridis', lname)
        map3 = psmap(land, 'plasma', lname)

    elif map_type == 'Chloropleth Map':

        new = new[new['Country'] == selectedcountry]
        new = new.groupby(['Region'])[name].sum().reset_index()

        if selectedcountry == 'Austria':
            map = cmap(land,'properties.name:N','goldgreen','properties.iso',new,300,300,lname,name)
            map1 = cmap(land, 'properties.name:N', 'lightorange', 'properties.iso', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'lighttealblue', 'properties.iso', new, 300, 300, lname, name)
            map3 = cmap(land, 'properties.name:N', 'plasma', 'properties.iso', new, 300, 300, lname, name)
        elif selectedcountry == 'Norway':
            map = cmap(land, 'properties.fylkesnavn:N', 'goldgreen', 'properties.objectid', new, 300, 300,lname,name)
            map1 = cmap(land, 'properties.fylkesnavn:N', 'lightorange', 'properties.objectid', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.fylkesnavn:N', 'lighttealblue', 'properties.objectid', new, 300, 300, lname, name)
            map3 = cmap(land, 'properties.fylkesnavn:N', 'plasma', 'properties.objectid', new, 300, 300, lname,
                        name)

        elif selectedcountry == 'Germany':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'properties.short', new, 300, 300,lname,name)
            map1 = cmap(land, 'properties.name:N', 'lightorange', 'properties.short', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'lighttealblue', 'properties.short', new, 300, 300, lname, name)
            map3 = cmap(land, 'properties.name:N', 'plasma', 'properties.short', new, 300, 300, lname, name)

        elif selectedcountry == 'Slovak':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'id', new, 300, 300,lname,name)
            map1 = cmap(land, 'properties.name:N', 'lightorange', 'id', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'lighttealblue', 'id', new, 300, 300, lname, name)
            map3 = cmap(land, 'properties.name:N', 'plasma', 'id', new, 300, 300, lname, name)

        elif selectedcountry == 'Hungary':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'id', new, 300, 300,lname,name)
            map1 = cmap(land, 'properties.name:N', 'lightorange', 'id', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'lighttealblue', 'id', new, 300, 300,lname,name)
            map3 = cmap(land, 'properties.name:N', 'plasma', 'id', new, 300, 300, lname, name)


        elif selectedcountry == 'France':
            map = cmap(land, 'properties.ID:N', 'goldgreen', 'properties.ID', new, 380, 350,lname,name)
            map1 = cmap(land, 'properties.ID:N', 'lightorange', 'properties.ID', new, 380, 350, lname, name)
            map2 = cmap(land, 'properties.ID:N', 'lighttealblue', 'properties.ID', new, 380, 350, lname, name)
            map3 = cmap(land, 'properties.ID:N', 'plasma', 'properties.ID', new, 380, 350, lname, name)

        elif selectedcountry == 'Switzerland':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'properties.id', new, 300, 300,lname,name)
            map1 = cmap(land, 'properties.name:N', 'lightorange', 'properties.id', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'lighttealblue', 'properties.id', new, 300, 300, lname, name)
            map3 = cmap(land, 'properties.name:N', 'plasma', 'properties.id', new, 300, 300, lname, name)


        elif selectedcountry == 'Italy' or 'Sweden' or  'Poland' or "spain" or 'Romania' or 'Czech republic':
            map = cmap(land, 'properties.NAME_1:N', 'goldgreen', 'properties.ID_1', new, 350, 300,lname,name)
            map1 = cmap(land, 'properties.NAME_1:N', 'lightorange', 'properties.ID_1', new, 350, 300, lname, name)
            map2 = cmap(land, 'properties.NAME_1:N', 'lighttealblue', 'properties.ID_1', new, 350, 300, lname, name)
            map3 = cmap(land, 'properties.NAME_1:N', 'plasma', 'properties.ID_1', new, 350, 300, lname, name)


    if selectedcountry == 'Slovak':
        overview = alt.layer(
            alt.Chart(europe).mark_geoshape(
                fill='lightgray', stroke='white', strokeWidth=0.25
            ).encode(
            ),
            alt.Chart(europe).mark_geoshape().transform_filter(
                alt.FieldEqualPredicate(field='properties.geounit', equal='Slovakia')

            ).encode(
                color=alt.value('yellow')
            )
        ).project(
            type='mercator', scale=380, translate=[100, 550]
        ).properties(
            width=300,
            height=320
        ).configure_view(
            stroke=None
        )
    elif selectedcountry == 'Czech republic':
        overview = alt.layer(
            alt.Chart(europe).mark_geoshape(
                fill='lightgray', stroke='white', strokeWidth=0.25
            ).encode(
            ),
            alt.Chart(europe).mark_geoshape().transform_filter(
                alt.FieldEqualPredicate(field='properties.geounit', equal='CzechRepublic')

            ).encode(
                color=alt.value('yellow')
            )
        ).project(
            type='mercator', scale=380, translate=[100, 550]
        ).properties(
            width=300,
            height=320
        ).configure_view(
            stroke=None
        )
    else:
        overview = alt.layer(
            alt.Chart(europe).mark_geoshape(
                fill='lightgray', stroke='white', strokeWidth=0.25
            ).encode(
            ),
            alt.Chart(europe).mark_geoshape().transform_filter(
                alt.FieldEqualPredicate(field='properties.geounit', equal=selectedcountry)

            ).encode(
                color=alt.value('yellow')
            )
        ).project(
            type='mercator', scale=380, translate=[100, 550]
        ).properties(
            width=300,
            height=320
        ).configure_view(
            stroke=None
        )

    col1, col2,col3 = st.columns([1.4,1.5,1.5])

    with col1:
        st.subheader("Europe")
        st.altair_chart(overview)

    with col2:
        st.subheader(selectedcountry)
        st.altair_chart(map, use_container_width=True)
        st.altair_chart(map3, use_container_width=True)
    with col3:
        st.altair_chart(map1, use_container_width=True)
        st.altair_chart(map2, use_container_width=True)
else:
    st.altair_chart(lakes, use_container_width=True)





