# Examples for DeTrusty

This directory contains queries and source descriptions for the CoyPu and K4COVID examples mentioned in the [documentation](https://sdm-tib.github.io/DeTrusty/library.html#executing-queries).

The example data is organized as follows:

- `CoyPu` - Example for the project [CoyPu](https://coypu.org/)
  - `Q1.rq` - Life expectancy for all countries in 2017 as reported by World Bank and Wikidata
  - `Q2.rq` - GDP per capita and carbon emission per capita for Germany per year
  - `rdfmts.json` - source description for CoyPu (Wikidata and World Bank)
- `K4COVID` - Examples form the Knowledge4COVID-19 paper [1]
  - `Q1.rq` - "Retrieve from DBpedia the excretion rate, metabolism, and routes of administration of the COVID-19 drugs in the treatments to treat COVID-19 in patients with Asthma."
  - `Q2.rq` - "Retrieve from Wikidata the CheMBL code, metabolism, and routes of administration of the COVID-19 drugs in the treatments to treat COVID-19 in patients with a cardiopathy."
  - `Q3.rq` - "Retrieve from DBpedia the excretion rate, metabolism, and routes of administration, CheMBL and Kegg codes, smile notation, and trade name of the COVID-19 drugs in the treatments to treat COVID-19 in patients with Asthma."
  - `Q4.rq` - "Retrieve from DBpedia the disease label, ICD-10 and mesh codes, and risks of the comorbidities of the COVID-19 treatments."
  - `Q5.rq` - "Retrieve the COVID-19 and comorbidity drugs on a treatment and the CheMBL code, mass, and excretion route for the comorbidity drugs." 
  - `rdfmts.json` - source description for K4COVID (DBpedia, Wikidata, and K4COVID KG)
- `docker-compose.yml` - Example to set up DeTrusty as a Docker-based service using the K4COVID use case. 

## References
1. Ahmad Sakor, Samaneh Jozashoori, Emetis Niazmand, Ariam Rivas, Kostantinos Bougiatiotis, Fotis Aisopos, Enrique Iglesias, Philipp D. Rohde, Trupti Padiya, Anastasia Krithara, Georgios Paliouras, Maria-Esther Vidal. Knowledge4COVID-19: A Semantic-based Approach for Constructing a COVID-19 related Knowledge Graph from Various Sources and Analysing Treatments' Toxicities. In _Journal of Web Semantics Volume 75_. [https://doi.org/10.1016/j.websem.2022.100760](https://doi.org/10.1016/j.websem.2022.100760) 
