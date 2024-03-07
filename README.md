# SOCI-40133-Final-Project

This repository contains Jiazheng Li (jiazheng123@uchicago.edu), Tianyue Cong (tianyuec@uchicago.edu), and Weiwu Yan's (weiwuyan@uchicago.edu) code for SOCI 40133 Computational Content Analysis final project that examines:
1) difference in funding received across subfields under NSF division of Behavioral and Cognitive Sciences;
2) temporald dynamics of topic prevalence from 2011 to 2020;
3) the impact of research funding on awarded authors' research topical diversity.

## Github Repo Navigation
The following is the **top-level directory layout** of this repo:

    .
    ├── cluster/                         # Cluster authors based on tf-idf vectors of paper abstract
    ├── collaboration_network/           # Build collaboration network of awarded authors
    ├── data_processing/                 # Preprocess the data ready for analysis
    ├── database/                        # Database storing the data for analysis
    ├── research diversity/              # Examine the impact of NSF funding on research topical diversity
    ├── .gitattributes
    ├── .gitignore
    ├── README.md
    └── Structural Topic Modeling.Rmd    # Conduct structual topic modeling

## Workflow
This project began by leveraging helper functions in [data_processing](data_processing) to store different csv files ready for data analysis. Then, we performed [clustering](cluster) of awarded authors based on ti-idf vectors of paper abstract. Following that, we performed [structural topic modeling](Structural Topic Modeling.Rmd) to examine changes in topic prevalence from 2011 to 2020. Finally, we performed [within-person test of research diversity](research_diversity) to test the effect of NSF funding on awarded authors' topical diversity. 

Note: we also tried to build [collaboration network](collaboration_network) and examined changes in (network) centrality measures. But unfortunately, we did not find any significant differences, so we did not include them in the final paper (also given already sufficient amount of content). However, we still decided to put this in the repo for reference.  
