# -*- coding: utf-8 -*-
"""Reading from SRA.
"""
import math
import os
from evac.utils import *
from ngs import NGS
from ngs.Read import Read
from ngs.ErrorMsg import ErrorMsg

def sra_reader(accn, batcher):
    """Iterates through a read collection for a given accession number using
    the ngs-lib python bindings.
    
    Args:
        accn: The accession number
        batch_size: The maximum number of reads to request in each call to SRA
        max_reads: The total number of reads to process, or all reads in the
            SRA run if None
    
    Yields:
        Each pair of reads (see ``sra_read_pair``)
    """
    with NGS.openReadCollection(accn) as run:
        run_name = run.getName()
        read_count = run.getReadCount()
        for batch, start, size in batcher(read_count):
            with run.getReadRange(start + 1, size, Read.all) as read:
                for read_idx in range(size):
                    read.nextRead()
                    yield sra_read(read)

def sra_read(read, paired=None, expected_fragments=None):
    """Creates sequence of (name, sequence, qualities) tuples from the current
    read of an ngs.ReadIterator. Typically the sequence has one or two tuples
    for single- and paired-end reads, respectively.
    """
    read_name = read.getReadName()
    num_fragments = read.getNumFragments()
    if expected_fragments and num_fragments != expected_fragments:
        raise Exception("Read {} has fewer than {} fragments".format(
            read_name, expected_fragments))
    # TODO: extract other useful information such as read group
    #read_group = read.getReadGroup()
    
    def next_frag():
        read.nextFragment()
        if paired and not read.isPaired():
            raise Exception("Read {} is not paired".format(read_name))
        return (
            read_name,
            read.getFragmentBases(),
            read.getFragmentQualities())
    
    return tuple(next_frag() for i in range(num_fragments))
