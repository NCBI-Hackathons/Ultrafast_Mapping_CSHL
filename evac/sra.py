# -*- coding: utf-8 -*-
"""Reading from SRA.
"""
import math
import os
from ngs import NGS
from ngs.Read import Read
from ngs.ErrorMsg import ErrorMsg
from xphyle import open_

class Batcher(object):
    """Iterator over batches of items.
    
    Args:
        item_start: The first item to return
        item_stop: The last item to return, or None for all items
        item_limit: The maximum number of items to return
        batch_start: The first batch to return
        batch_stop: The last batch to return
        batch_size: The size of each batch
        batch_step: The number of batches to skip over on each iteration
        progress: Wrap the iterator in a progress bar (if tqdm is available)
    
    The item-level limits override the batch-level limits. The actual number of
    batches generated is:
    
    min(
        ceil(min(item_limit, (item_stop-item_start)) / batch_size),
        len(range(batch_start, batch_stop, batch_step))
    )
    
    Yields:
        Tuple of (batch_number, start index, batch size), where batch number and
        start index are both 0-based. The later two can be used to index into a
        sequence (e.g. list[start:(start+size)]).
    """
    def __init__(self, item_start=0, item_stop=None, item_limit=None,
                 batch_start=0, batch_stop=None, batch_size=1000,
                 batch_step=1, progress=True):
        self.item_start = item_start
        self.item_stop = item_stop
        self.item_limit = item_limit
        self.batch_start = batch_start
        self.batch_stop = batch_stop
        self.batch_size = batch_size
        self.batch_step = batch_step
        self.progress = progress
    
    def __call__(self, total, progress=False):
        # determine the last read in the slice
        stop = min(total, self.item_stop) if self.item_stop else total
        # enumerate the batch start indices
        starts = list(range(self.item_start, stop, self.batch_size))
        # subset batches
        batch_stop = len(starts)
        if self.batch_stop:
            batch_stop = min(batch_stop, self.batch_stop)
        starts = starts[self.batch_start:batch_stop:self.batch_step]
        # determine the max number of items
        limit = min(len(starts) * self.batch_size, total)
        if self.item_limit:
            limit = min(limit, self.item_limit)
        # determine the number of batches based on the number of items
        batches = math.ceil(limit / self.batch_size)
        if batches < len(starts):
            starts = starts[:batches]
        # iterate over starts, possibly wrapping with a progress bar
        itr = starts
        if self.progress:
            itr = wrap_progress(itr, total=max_batches)
        # yield batch_num, batch_start, batch_size tuples
        for batch_num, start in enumerate(itr):
            size = self.batch_size
            if batch_num == (batches-1):
                size = limit - (batch_num * size)
            yield (batch_num, start, size)

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
