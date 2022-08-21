import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="The Ramsey Highlights", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child{
        width: 260px;
    }
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child{
        width: 260px;
        height: 800px;
        margin-left: 0px;
        margin-top: -60px;
        margin-bottom: 0px
    }

    """,
    unsafe_allow_html=True,
)

padding_top = 0
padding_bottom = 10
padding_left = 3
padding_right = 3
st.markdown(f'''
            <style>
                 .appview-container .main .block-container{{
                          padding-top: {padding_top}rem; 
                          padding-left: {padding_left}rem;
                          padding-right: {padding_right}rem;
                          padding-bottom: {padding_bottom}rem;

                 }}
            </style>
            ''',
            unsafe_allow_html=True,
            )

# europe = alt.topo_feature("https://raw.githubusercontent.com/deldersveld/topojson/master/continents/europe.json",'continent_Europe_subunits')
ordinates = pd.read_csv("C:\\Users\\Jutta\\Downloads\\Bachelorarbeit\\1-s2.0-S0160412021004463-mmc1.csv")
europe = alt.topo_feature('https://vega.github.io/vega-datasets/data/world-110m.json', 'countries')

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
        map_type = st.radio("Please select the map type:", ('Proportional symbol map', 'Chloropleth Map'))
        if map_type == 'Chloropleth Map':
            compare_country = st.selectbox(
                'Which countries you want to compare?',
                options=countries
            )

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
po.set_index('Unnamed: 0', inplace=True)
new = pd.concat([new, po], axis=1, join='inner')
hover = alt.selection(type='single', on='click', empty='all')


def lakemap(europe, lname):
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
    ).properties(
        width=1000,
        height=590
    ).project(
        type='mercator', scale=700, translate=[300, 1000]
    ).configure_view(
        stroke=None
    )


lakes = lakemap(europe, lname)


def overviewmap(id):
    return alt.layer(
        alt.Chart(europe).mark_geoshape(
            fill='lightgray', stroke='black', strokeWidth=0.25
        ).encode(
        ),
        alt.Chart(europe).mark_geoshape().transform_filter(
            alt.FieldEqualPredicate(field='id', equal=id)
        ).encode(
            color=alt.value('yellow')
        )
    ).project(
        type='mercator', scale=250, translate=[50, 350]
    ).properties(
        width=220,
        height=220
    ).configure_view(
        stroke=None
    )


def coverviewmap(id, id1):
    return alt.layer(
        alt.Chart(europe).mark_geoshape(
            fill='lightgray', stroke='black', strokeWidth=0.25
        ).encode(
        ),
        alt.Chart(europe).mark_geoshape().transform_filter(
            alt.FieldOneOfPredicate(field='id', oneOf=[id, id1])
        ).encode(
            color=alt.Color('id:Q', legend=None)
        )
    ).project(
        type='mercator', scale=250, translate=[50, 350]
    ).properties(
        width=220,
        height=220
    ).configure_view(
        stroke=None
    )


def psmap(land, color, lname):
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
        height=500
    ).configure_view(
        stroke=None
    ).configure_legend(
        orient='bottom',
        labelLimit=115
    )


def cmap(land, tooltip, color, lookup, data, width, height, lname, name):
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
        ),
    ).properties(
        width=width,
        height=height
    ).configure_view(
        stroke=None
    ).configure_legend(
        orient='top'
    )


def ccmap(land, tooltip, color, lookup, data, width, height, lname, name):
    return alt.layer(
        alt.Chart(land).mark_geoshape(
            fill='lightgray', stroke='white', strokeWidth=0.25
        ).encode(
        ),
        alt.Chart(land).mark_geoshape().encode(
            tooltip=[alt.Tooltip(lname), alt.Tooltip(tooltip)],
            color=alt.Color(lname, scale=alt.Scale(scheme=color), legend=None)
        ).transform_lookup(
            lookup=lookup,
            from_=alt.LookupData(data=data, key='Region',
                                 fields=[name])
        ),
    ).properties(
        width=width,
        height=height
    ).configure_view(
        stroke=None
    )


if show:
    Austria = alt.topo_feature(
        "https://raw.githubusercontent.com/ginseng666/GeoJSON-TopoJSON-Austria/master/2021/simplified-99.9/laender_999_topo.json",
        'laender')
    Germany = alt.topo_feature(
        "https://raw.githubusercontent.com/AliceWi/TopoJSON-Germany/master/germany.json",
        'states')
    Italy = alt.topo_feature(
        "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/italy/italy-regions.json",
        'ITA_adm1')
    Switzerland = alt.topo_feature("https://raw.githubusercontent.com/samateja/D3topoJson/master/switzerland.json",
                                   'switzerland')
    Norway = alt.topo_feature(
        "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/norway/norway-new-counties.json",
        'Fylker')
    Sweden = alt.topo_feature(
        "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/sweden/sweden-counties.json",
        'SWE_adm1')
    Poland = alt.topo_feature(
        "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/poland/poland-provinces.json",
        'POL_adm1')
    Slovak = alt.topo_feature("https://raw.githubusercontent.com/mlajtos/slovakia-topojson/master/slovakia.json",
                              'kraje')
    Hungary = alt.topo_feature("https://code.highcharts.com/mapdata/countries/hu/hu-all.topo.json", 'default')

    Romania = alt.topo_feature(
        "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/romania/romania-counties.json",
        'ROU_adm1')
    Czechrepublic = alt.topo_feature(
        "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/czech-republic/czech-republic-regions.json",
        'CZE_adm1')
    France = alt.topo_feature(
        "https://raw.githubusercontent.com/AtelierCartographie/Khartis/master/public/data/map/FR-reg-2016/france.json",
        'poly')
    Spain = alt.topo_feature(
        "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/spain/spain-comunidad.json",
        'ESP_adm1')

    if selectedcountry == 'Austria':
        overview = overviewmap(40)
        land = Austria
    elif selectedcountry == 'Germany':
        overview = overviewmap(276)
        land = Germany
    elif selectedcountry == 'Italy':
        overview = overviewmap(380)
        land = Italy
    elif selectedcountry == 'Switzerland':
        overview = overviewmap(756)
        land = Switzerland
    elif selectedcountry == 'Norway':
        overview = overviewmap(578)
        land = Norway
    elif selectedcountry == 'Sweden':
        overview = overviewmap(752)
        land = Sweden
    elif selectedcountry == 'Poland':
        overview = overviewmap(616)
        land = Poland
    elif selectedcountry == 'Slovak':
        overview = overviewmap(703)
        land = Slovak
    elif selectedcountry == 'Hungary':
        overview = overviewmap(348)
        land = Hungary
    elif selectedcountry == 'Romania':
        overview = overviewmap(642)
        land = Romania
    elif selectedcountry == 'Czech republic':
        overview = overviewmap(203)
        land = Czechrepublic
    elif selectedcountry == 'France':
        overview = overviewmap(250)
        land = France
    elif selectedcountry == 'Spain':
        overview = overviewmap(724)
        land = Spain

    if map_type == 'Proportional symbol map':
        map = psmap(land, 'goldgreen', lname)
        map1 = psmap(land, 'purplered', lname)
        map2 = psmap(land, 'viridis', lname)
        map3 = psmap(land, 'plasma', lname)
        with st.container():
            st.subheader("Europe")
            st.altair_chart(overview)
            st.subheader(selectedcountry)
            st.altair_chart(map, use_container_width=True)

    elif map_type == 'Chloropleth Map':
        if compare_country == 'Austria':
            land1 = Austria
        elif compare_country == 'Germany':
            land1 = Germany
        elif compare_country == 'Italy':
            land1 = Italy
        elif compare_country == 'Switzerland':
            land1 = Switzerland
        elif compare_country == 'Norway':
            land1 = Norway
        elif compare_country == 'Sweden':
            land1 = Sweden
        elif compare_country == 'Poland':
            land1 = Poland
        elif compare_country == 'Slovak':
            land1 = Slovak
        elif compare_country == 'Hungary':
            land1 = Hungary
        elif compare_country == 'Romania':
            land1 = Romania
        elif compare_country == 'Czech republic':
            land1 = Czechrepublic
        elif compare_country == 'France':
            land1 = France
        else:
            land1 = Spain

        data = [{'Austria': 40, 'Germany': 276, 'Italy': 380, 'Switzerland': 756, 'Norway': 578, 'Sweden': 752,
                 'Poland': 616, 'Slovak': 703, 'Hungary': 348, 'Romania': 642, 'Czech republic': 203, 'France': 250,
                 'Spain': 724}]
        compare = pd.DataFrame(data)
        overview = coverviewmap(compare.loc[0, selectedcountry], compare.loc[0, compare_country])

        new1 = new
        new = new[new['Country'] == selectedcountry]
        new = new.groupby(['Region'])[name].sum().reset_index()

        new1 = new1[new1['Country'] == compare_country]
        new1 = new1.groupby(['Region'])[name].sum().reset_index()

        if selectedcountry == 'Austria':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'properties.iso', new, 250, 250, lname, name)
            map2 = cmap(land, 'properties.name:N', 'plasma', 'properties.iso', new, 250, 250, lname, name)
        elif selectedcountry == 'Norway':
            map = cmap(land, 'properties.fylkesnavn:N', 'goldgreen', 'properties.objectid', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.fylkesnavn:N', 'plasma', 'properties.objectid', new, 300, 300, lname, name)
        elif selectedcountry == 'Germany':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'properties.short', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'plasma', 'properties.short', new, 300, 300, lname, name)
        elif selectedcountry == 'Slovak':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'id', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'plasma', 'id', new, 300, 300, lname, name)
        elif selectedcountry == 'Hungary':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'id', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'plasma', 'id', new, 300, 300, lname, name)
        elif selectedcountry == 'France':
            map = cmap(land, 'properties.ID:N', 'goldgreen', 'properties.ID', new, 380, 350, lname, name)
            map2 = cmap(land, 'properties.ID:N', 'plasma', 'properties.ID', new, 380, 350, lname, name)
        elif selectedcountry == 'Switzerland':
            map = cmap(land, 'properties.name:N', 'goldgreen', 'properties.id', new, 300, 300, lname, name)
            map2 = cmap(land, 'properties.name:N', 'plasma', 'properties.id', new, 300, 300, lname, name)
        elif selectedcountry == 'Italy' or 'Sweden' or 'Poland' or "spain" or 'Romania' or 'Czech republic':
            map = cmap(land, 'properties.NAME_1:N', 'goldgreen', 'properties.ID_1', new, 350, 300, lname, name)
            map2 = cmap(land, 'properties.NAME_1:N', 'plasma', 'properties.ID_1', new, 350, 300, lname, name)

        if compare_country == 'Austria':
            map1 = ccmap(land1, 'properties.name:N', 'goldgreen', 'properties.iso', new1, 250, 250, lname, name)
            map3 = ccmap(land1, 'properties.name:N', 'plasma', 'properties.iso', new1, 250, 250, lname, name)
        elif compare_country == 'Germany':
            map1 = ccmap(land1, 'properties.name:N', 'goldgreen', 'properties.short', new1, 300, 300, lname, name)
            map3 = ccmap(land1, 'properties.name:N', 'plasma', 'properties.short', new1, 300, 300, lname, name)
        elif compare_country == 'Norway':
            map1 = ccmap(land1, 'properties.fylkesnavn:N', 'goldgreen', 'properties.objectid', new1, 300, 300, lname,
                         name)
            map3 = ccmap(land1, 'properties.fylkesnavn:N', 'plasma', 'properties.objectid', new1, 300, 300, lname, name)
        elif compare_country == 'Slovak':
            map1 = ccmap(land1, 'properties.name:N', 'goldgreen', 'id', new1, 300, 300, lname, name)
            map3 = ccmap(land1, 'properties.name:N', 'plasma', 'id', new1, 300, 300, lname, name)
        elif compare_country == 'Hungary':
            map1 = ccmap(land1, 'properties.name:N', 'goldgreen', 'id', new1, 300, 300, lname, name)
            map3 = ccmap(land1, 'properties.name:N', 'plasma', 'id', new1, 300, 300, lname, name)
        elif compare_country == 'France':
            map1 = ccmap(land1, 'properties.ID:N', 'goldgreen', 'properties.ID', new1, 380, 350, lname, name)
            map3 = ccmap(land1, 'properties.ID:N', 'plasma', 'properties.ID', new1, 380, 350, lname, name)

        elif compare_country == 'Switzerland':
            map1 = ccmap(land1, 'properties.name:N', 'goldgreen', 'properties.id', new1, 300, 300, lname, name)
            map3 = ccmap(land1, 'properties.name:N', 'plasma', 'properties.id', new1, 300, 300, lname, name)

        elif compare_country == 'Italy' or 'Sweden' or 'Poland' or "spain" or 'Romania' or 'Czech republic':
            map1 = ccmap(land1, 'properties.NAME_1:N', 'goldgreen', 'properties.ID_1', new1, 350, 300, lname, name)
            map3 = ccmap(land1, 'properties.NAME_1:N', 'plasma', 'properties.ID_1', new1, 350, 300, lname, name)

        col4, col5 = st.columns([1, 3])
        with col4:
            st.subheader("Europe")
            st.altair_chart(overview)

        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader(selectedcountry)
            st.altair_chart(map, use_container_width=True)
            st.altair_chart(map2, use_container_width=True)
        with col2:
            st.subheader(compare_country)
            st.altair_chart(map1, use_container_width=True)
            st.altair_chart(map3, use_container_width=True)


else:
    with st.container():
        st.altair_chart(lakes, use_container_width=True)





