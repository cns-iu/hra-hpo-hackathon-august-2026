library(tidyverse)


liver_cts = read.table('Desktop/HackathonHRA/hra_asctb_liver.csv', skip = 10, fill = TRUE, header = TRUE, sep = ',')

liver_cts[liver_cts == ""] = NA
liver_cts$CT.1.ID |> unique()
liver_cts$CT.1.LABEL |> unique()


tabula_data = read.table('Desktop/HackathonHRA/tabula_sapiens_cell_ontology_map.tsv', fill = TRUE, sep = '\t', header = TRUE)
intersect(tabula_data$cell_ontology_id, liver_cts$CT.1.ID)

intersect(tabula_data$cell_ontology_id, liver_cts$CT.1.ID) |> length()
intersect(tabula_data$cell_ontology_id, liver_cts$CT.1.ID)
intersect(tabula_data$cell_ontology_class, liver_cts$CT.1.LABEL)
