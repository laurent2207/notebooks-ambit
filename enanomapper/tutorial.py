#!/usr/bin/env python
# coding: utf-8

# # eNanoMapper API guide

# ## eNanoMapper database background

# - FP7 project eNanoMapper http://www.enanomapper.net/
# - eNanoMapper database implementation: AMBIT software http://ambit.sf.net
# - publication https://www.beilstein-journals.org/bjnano/articles/6/165
# - eNanoMapper prototype database https://data.enanomapper.net 

# ## Nanosafety data 

# - NanoSafety data compiled in eNanoMapper databases: https://search.data.enanomapper.net/ 
# - Each project data is imported into one eNanoMapper instance, e.g. https://apps.ideaconsult.net/nanoreg1  
#   - AMBIT REST API 
# - Aggregated search view across multiple databases are available at https://search.data.enanomapper.net 
#   - Solr REST API

# ## eNanoMapper data model

# ![data model](http://ambit.sourceforge.net/enanomapper/templates/images/data_model.png)
# http://ambit.sourceforge.net/enanomapper/templates/convertor_how.html

# ## eNanoMapper database API

# Swagger API docs at http://enanomapper.github.io/API/
from solrscope import aa
import ipywidgets as widgets
from ipywidgets import interact, interactive, fixed, interact_manual
from importlib import reload
from solrscope import client_solr
from solrscope import client_ambit
from solrscope import annotation
import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings("ignore")

print('Select eNanoMapper database instance:')

#config="enanomapper_private.yaml"
config="enanomapper_public.yaml"
#config="enm_composite_private.yaml"

def search_service_protected(url,apikey):
    return (url,apikey)
def search_service_open(url):
    return (url)    


style = {'description_width': 'initial'}
config,config_servers, config_security, auth_object, msg = aa.parseOpenAPI3(config=config)    
service_widget = widgets.Dropdown(
    options=config_servers['url'],
    description='Service:',
    disabled=False,
    style=style
)
if config_security is None:
    service = interactive(search_service_open,url=service_widget)
else:
    print(msg)
    apikey_widget=widgets.Text(
            placeholder='',
            description=config_security,
            disabled=False,
            style=style
    )    
    service = interactive(search_service_protected,url=service_widget,apikey=apikey_widget)    

display(service)

# ### What is in the database ?
service_uri=service_widget.value
if auth_object != None:
    auth_object.setKey(apikey_widget.value)

cli_facets = client_ambit.AMBITFacets(service_uri)
r = cli_facets.get(page=0,pagesize=1000,auth=auth_object)
if r.status_code==200:

    facets = cli_facets.parse(r.json())    
    print(json.dumps(facets, indent=4))   
else:
    facets = None
    print(r.status_code)

df=pd.DataFrame(facets)
display(df[["subcategory","endpoint","value","count"]])

#endpoints
cli_facets = client_ambit.AMBITFacets(service_uri,key="/experiment_endpoints")

r = cli_facets.get(page=0,pagesize=100,params={"top":"TOX"},auth=auth_object)
if r.status_code==200:

    facets = cli_facets.parse(r.json())    
    #print(json.dumps(facets, indent=4))   
    df=pd.DataFrame(facets)
    display(df)
else:
    substances = None
    print(r.status_code)

# ###  Substance queries
# #### All gold nanoparticles

materialtype="NPO_401"

a = annotation.DictionarySubstancetypes()
print(">>> Looking for {}".format(a.annotate(materialtype)))

service_uri=service_widget.value

cli_materials = client_ambit.AMBITSubstance(service_uri)
r = cli_materials.get(params={'search': materialtype,'type' : 'substancetype'},page=0,pagesize=10,auth=auth_object)
if r.status_code==200:

    substances = cli_materials.parse(r.json())    
    print(json.dumps(substances, indent=4))    
else:
    substances = None
    print(r.status_code)

# #### Retrieve physchem data for selected substances

endpointcategory='PC_GRANULOMETRY_SECTION'
a = annotation.DictionaryEndpointCategory()
print(">>> Looking for {}".format(a.annotate(endpointcategory)))

for substance in substances:
    print(substance['URI'])    
    cli = client_ambit.AMBITSubstanceStudy(substance['URI'])
    r = cli.get(params={'category': endpointcategory,'top' : 'P-CHEM'},page=0,pagesize=10,auth=auth_object)
    #print(r.json())
    print(json.dumps(r.json(), indent=4))    

# #### Substance compositions

reload(client_ambit)
for substance in substances:
  
    print(substance['URI'])    
    cli = client_ambit.AMBITSubstanceComposition(substance['URI'])
    r = cli.get(auth=auth_object)
    compositions = cli.parse(r.json())
    for composition in compositions:
        print("-------------------------------------------------------------------------")
        print(composition['relation'])
        print(composition['proportion'])        
        print(composition['component']['compound']['cas'])
        print(composition['component']['compound']['name'])
        
        cli_cmp = client_ambit.AMBITCompound(root_uri=composition['component']['compound']['URI'],resource=None)
        response = cli_cmp.get(media="chemical/x-mdl-sdfile",pagesize=1)
        
        if response.status_code == 200:
            print(response.text) 
            

# #### Investigation
# results in a tabular form

reload(client_ambit)
cli_investigation= client_ambit.AMBITInvestigation(service_uri)
r = cli_investigation.get(params={'search': endpointcategory,'type' : 'bystudytype'},page=0,pagesize=100,auth=auth_object)
if r.status_code==200:

    results = cli_investigation.parse(r.json())    
    print(json.dumps(results, indent=4))    
else:
    df=None
    print(r.status_code)

df=pd.DataFrame(results)
display(df.head())

# # Aggregated search
# - Using Solr-powered free text and faceted search over several eNanoMapper database instances
# - see https://search.data.enanomapper.net (web app) and  https://api.ideaconsult.net for API access

# ### Service selection

print('Select enanoMapper aggregated search service:')
style = {'description_width': 'initial'}
config,config_servers, config_security, auth_object, msg = aa.parseOpenAPI3()    
service_widget = widgets.Dropdown(
    options=config_servers['url'],
    description='Service:',
    disabled=False,
    style=style
)
if config_security is None:
    service = interactive(search_service_open,url=service_widget)
else:
    print(msg)
    apikey_widget=widgets.Text(
            placeholder='',
            description=config_security,
            disabled=False,
            style=style
    )    
    service = interactive(search_service_protected,url=service_widget,apikey=apikey_widget)    

display(service)

service_uri=service_widget.value
print("Sending queries to {}".format(service_uri))
if auth_object!=None:
    auth_object.setKey(apikey_widget.value)

# ### Faceted search 

# #### [Facets] Number of substances per project

facets = client_solr.Facets()
query=facets.getQuery(query="*:*",facets=["dbtag_hss"],fq="type_s:substance")
#print(query)
r = client_solr.post(service_uri,query=query,auth=auth_object)
response_json=r.json()
print(response_json)
if r.status_code==200:
    facets.parse(response_json['facets'])
else:
    print(r.status_code)

# #### [Facets] Number of material types per project

query=facets.getQuery(query="*:*",facets=["dbtag_hss","substanceType_hs"],fq="type_s:substance")
#print(query)
r = client_solr.post(service_uri,query=query,auth=auth_object)
response_json=r.json()
if r.status_code==200:
    facets.parse(response_json['facets'])
else:
    print(r.status_code)

a = annotation.DictionarySubstancetypes()
term=a.annotate("NPO_354")
print(term)
term=a.annotate("NPO_1373")
print(term)


# #### [Facets] Get all cell types

reload(client_solr)

facets = client_solr.Facets()
query=facets.getQuery(query="*:*",facets=["E.cell_type_s"],fq="type_s:params")
#print(query)
r = client_solr.post(service_uri,query=query,auth=auth_object)
response_json=r.json()
if r.status_code==200:
    facets.parse(response_json['facets'])
else:
    print(r.status_code)

# #### [Facets] Get all protocols per endpoint for titanium dioxide nanoparticles (NPO_1486)

fields=["topcategory_s","endpointcategory_s","guidance_s"]
query=facets.getQuery(query="substanceType_s:NPO_1486",fq="type_s:study",facets=fields)
print(query)
r = client_solr.post(service_uri,query=query,auth=auth_object)
print(r.status_code)
if r.status_code==200:
    facets.parse(r.json()['facets'])
else:
    print(r.status_code)

# #### [Facets] Get all methods

fields=["topcategory_s","endpointcategory_s","E.method_s","E.sop_reference_s"]
query=facets.getQuery(query="*:*",fq="type_s:params",facets=fields)
print(query)
r = client_solr.post(service_uri,query=query,auth=auth_object)
print(r.status_code)
if r.status_code==200:
    facets.parse(r.json()['facets'])
else:
    print(r.status_code)

# #### [Facets] Get all material types

fields=["substanceType_hs","publicname_hs","name_hs","dbtag_hss"]
query=facets.getQuery(fq="type_s:substance",facets=fields)
#print(query)
r = client_solr.post(service_uri,query=query,auth=auth_object)
print(r.status_code)
if r.status_code==200:
    facets.parse(r.json()['facets'])
else:
    print(r.status_code)

# #### [Facets]  Get all endpoints for nanotubes

query=facets.getQuery(query="carbon nanotube",facets=["topcategory_s","endpointcategory_s","effectendpoint_s","unit_s"],fq="type_s:study")
#print(query)
r = client_solr.post(service_uri,query=query,auth=auth_object)
print(r.status_code)
#print(r.json()['facets'])
if r.status_code==200:
    facets.parse(r.json()['facets'])
else:
    print(r.status_code)

# ### Retrieve experimental data
# #### Physchem example - MWCNT size

reload(client_solr)
study = client_solr.StudyDocuments()
filter = {'topcategory_s':'P-CHEM', 'endpointcategory_s':'PC_GRANULOMETRY_SECTION' }
study.setStudyFilter(filter)
print(study.getSettings())
#all TiO2 NPO_1486
query = study.getQuery(textfilter='substanceType_s:NPO_354',rows=10000)
r = client_solr.post(service_uri,query=query,auth=auth_object)

#parse the data
if r.status_code==200:
    study = client_solr.StudyDocuments()
    rows = study.parse(r.json()['response']['docs'])
    df = study.rows2frame(rows)
    rows=None
    uuids = ['uuid.investigation','uuid.assay','uuid.document','uuid.substance']
    df.sort_values(by=uuids)
    display(df.head(50))
else:
    print(r.status_code)

#Group by material and endpoint
groups=[]

groups.append("m.public.name")
#groups.append("x.params.E.method")
#groups.append("p.guidance")
groups.append("x.params.MEDIUM")
groups.append("value.endpoint")
groups.append("value.endpoint_type")
groups.append("value.unit")
print(groups)

tmp=df.groupby(by=groups).agg({"value.range.lo" : ["mean","std","count"]}).reset_index()
(tmp)

# #### Tox example - TiO2 cell viability

reload(client_solr)
study = client_solr.StudyDocuments()
filter = {'topcategory_s':'TOX', 'endpointcategory_s':'ENM_0000068_SECTION' }
study.setStudyFilter(filter)
print(study.getSettings())
#all TiO2 NPO_1486
query = study.getQuery(textfilter='substanceType_s:NPO_354',rows=10000)
r = client_solr.post(service_uri,query=query,auth=auth_object)

#parse the data
if r.status_code==200:
    study = client_solr.StudyDocuments()
    rows = study.parse(r.json()['response']['docs'])
    df = study.rows2frame(rows)
    rows=None
    uuids = ['uuid.investigation','uuid.assay','uuid.document','uuid.substance']
    df.sort_values(by=uuids)
    display(df.head(50))
else:
    print(r.status_code)

groups=[]

groups.append("m.public.name")
groups.append("uuid.assay")
groups.append("uuid.document")
#groups.append("x.params.E.method")
#groups.append("p.guidance")
groups.append("x.params.MEDIUM")
groups.append("x.params.E.cell_type")
groups.append("x.conditions.material")
groups.append("value.endpoint")
groups.append("value.endpoint_type")
groups.append("value.unit")
print(groups)

tmp=df.groupby(by=groups).agg({"value.range.lo" : ["mean","std","count"]}).reset_index()
display(tmp)

# ## Annotation examples

reload(annotation)
a = annotation.DictionaryEndpoints()
for endpoint in ["CIRCULARITY","FERET_DIAMETER","IC50"]:
    term=a.annotate(endpoint)
    print(endpoint)
    print(term)
    print(a.getLink(term))

a = annotation.DictionaryCells()
for cell in ["3T3","A549"]:
    term=a.annotate(cell)
    print(cell)
    print(term)
    print(a.getLink(term))

a = annotation.DictionaryAssays()
for assay in ["CFE","Alamar blue","TEM","COMET"]:
    term=a.annotate(assay)
    print(assay)
    print(term)
    print(a.getLink(term))

a = annotation.DictionaryEndpointCategory()
term=a.annotate("PC_GRANULOMETRY_SECTION")
print(term)
print(a.getLink(term))

a = annotation.DictionarySpecies()
term=a.annotate("rat")
print(term)
print(a.getLink(term))

a = annotation.DictionarySubstancetypes()
term=a.annotate("NPO_401")
print(term)
