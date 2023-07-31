from simplesam import Reader

def get_sam_metrics(filename):
    in_file = open(filename, 'r')
    in_sam = Reader(in_file)

    binary_of_origin = list(in_sam.header['@PG'].keys())[0]
    command_line_list = in_sam.header['@PG'][binary_of_origin][2].split()  # suboptimal
    mapping_reference_file = command_line_list[command_line_list.index('-x') + 1] # reference file

    alignments = list()
    for x in in_sam:
        alignment = {}
        alignment["sequence_id"] = x.qname
        alignment["mapping_tags"] = x.tags
        alignment["position_in_ref"] = x.pos
        alignment["mapping_qual"] = x.mapq
        alignments.append(alignment)
        if (len(alignments) == 20):
            break

    binary_results = {}
    binary_results["binary_of_origin"] = binary_of_origin
    binary_results["mapping_reference_file"] = mapping_reference_file
    binary_results["alignments"] = alignments

    return binary_results