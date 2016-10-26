# -*- coding: utf-8 -*-
"""Reading from SRA.
"""
import os
from evac.utils import *
from ngs import NGS
from ngs.Read import Read
from ngs.ErrorMsg import ErrorMsg

def sra_read_pair(read_pair):
    """Creates a pair of tuples (name, sequence, qualities) from the current
    read of an ngs.ReadIterator.
    """
    read_name = read_pair.getReadName()
    if read_pair.getNumFragments() != 2:
        raise Exception("Read {} is not paired".format(read_name))
        
    read_group = read_pair.getReadGroup()
    
    read_pair.nextFragment()
    if not read_pair.isPaired():
        raise Exception("Read {} is not paired".format(read_name))
    read1 = (
        read_name,
        read_pair.getFragmentBases(),
        read_pair.getFragmentQualities())
    
    read_pair.nextFragment()
    if not read_pair.isPaired():
        raise Exception("Read {} is not paired".format(read_name))
    read2 = (
        read_name,
        read_pair.getFragmentBases(),
        read_pair.getFragmentQualities())
    
    return (read1, read2)

def sra_reader(accn, batch_size=1000, max_reads=None, progress=True):
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
    def run_iter(run, max_reads):
        run_name = run.getName()
        for batch_num, first_read in enumerate(
                range(1, max_reads, batch_size)):
            cur_batch_size = min(
                batch_size,
                max_reads - first_read + 1)
            with run.getReadRange(
                    first_read, cur_batch_size, Read.all) as read:
                for read_idx in range(cur_batch_size):
                    read.nextRead()
                    yield sra_read_pair(read)
    
    with NGS.openReadCollection(accn) as run:
        read_count = run.getReadCount()
        if max_reads:
            max_reads = min(read_count, max_reads)
        else:
            max_reads = read_count
        itr = run_iter(run, max_reads)
        for read_pair in wrap_progress(itr, disable=not progress, total=max_reads):
            yield read_pair
