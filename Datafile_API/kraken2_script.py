def get_kraken_metrics(output:str):
    file = open(output, 'r')
    lines = file.readlines()
    classifications = list()
    for line in lines:
        classification = {}
        values=line.strip().split("\t")
        classification["classified"] = values[0]
        classification["sequence_id"] = values[1]
        classification["taxonomy_id"]=values[2]
        #classification["sequence_length"]=values[3]
        classification["lca_mapping_list"]=values[4].split(" ")#is probably never used in plot but is there anyway
        classifications.append(classification)
        if(len(classifications)==20): #to be deleted for production
            break
    return classifications