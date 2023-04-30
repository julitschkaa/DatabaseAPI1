import os
import math
import zlib
from Bio import SeqIO
import pylab as plt
import numpy as np
import pandas as pd
import matplotlib.patches as patches

def get_fastq_metrics(filename):
    fastq_parser = SeqIO.parse(open(filename, "rt"), "fastq")
    reads = list()
    for record in fastq_parser:
        read = {}
        read["id"] = record.id
        read["sequence"] = record.seq
        read["phred_quality"] = record.letter_annotations["phred_quality"]
        reads.append(read)
    return reads
