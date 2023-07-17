from Bio import SeqIO

def get_fastq_metrics(filename):
    fastq_parser = SeqIO.parse(open(filename, "rt"), "fastq")
    reads = list()
    for record in fastq_parser:
        read = {}
        read["sequence_id"] = record.id
        read["sequence"] = str(record.seq)
        read["sequence_length"] = len(str(record.seq))
        read["min_quality"] = min(record.letter_annotations["phred_quality"])
        read["max_quality"] = max(record.letter_annotations["phred_quality"])
        read["average_quality"] = sum(record.letter_annotations["phred_quality"]) \
                                  / len(record.letter_annotations["phred_quality"])
        read["phred_quality"] = record.letter_annotations["phred_quality"]
        reads.append(read)
        #if(len(reads)==20): #input limit for test purpose
            #break
    return reads
