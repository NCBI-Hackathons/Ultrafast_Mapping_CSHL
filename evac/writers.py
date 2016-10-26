# -*- coding: utf-8 -*-
"""Writing to files.
"""
from contextlib import contextmanager
import copy
import io
import os
from evac.utils import *

class BatchWriter(object):
    """Wrapper for a string writer (e.g. FifoWriter) that improves performance
    by buffering a set number of reads and sending them as a single call to the
    string writer.
    
    Args:
        writer: The string writer to wrap. Must be callable with two arguments
            (read1 string, read2 string)
        batch_size: The size of the read buffer
        lines_per_row: The number of lines used by each read for the specific
            file format (should be passed by the subclass in a
            super().__init__ call)
        linesep: The separator to use between each line (defaults to os.linesep)
    """
    def __init__(self, writer, batch_size, lines_per_row, linesep=os.linesep):
        self.writer = writer
        self.batch_size = batch_size
        self.lines_per_row = lines_per_row
        self.bufsize = batch_size * lines_per_row
        self.linesep = linesep
        self.read1_batch = self._create_batch_list()
        self.read2_batch = copy.copy(self.read1_batch)
        self.index = 0
    
    def _create_batch_list(self):
        """Create the list to use for buffering reads. Can be overridden, but
        must return a list that is of size ``batch_size * lines_per_row``.
        """
        return [None] * self.bufsize
    
    def __call__(self, read1, read2):
        """Add a read pair to the buffer. Writes the batch to the underlying
        writer if the buffer is full.
        
        Args:
            read1: read1 tuple (name, sequence, qualities)
            read2: read2 tuple
        """
        self.add_to_batch(*read1, self.read1_batch, self.index)
        self.add_to_batch(*read2, self.read2_batch, self.index)
        self.index += self.lines_per_row
        if self.index >= self.bufsize:
            self.flush()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        if self.index > 0:
            self.flush()
        self.close()
    
    def flush(self):
        """Flush the current read buffers to the underlying string writer.
        
        Args:
            last: Is this the last call to flush? If not, a trailing linesep
                is written.
        """
        if self.index < self.bufsize:
            self.writer(
                self.linesep.join(self.read1_batch[0:self.index]),
                self.linesep.join(self.read2_batch[0:self.index]))
        else:
            self.writer(
                self.linesep.join(self.read1_batch),
                self.linesep.join(self.read2_batch))
        self.writer(self.linesep, self.linesep)
        self.index = 0
    
    def close(self):
        """Clear the buffers and close the underlying string writer.
        """
        self.read1_batch = None
        self.read2_batch = None
        self.writer.close()

class FastqWriter(BatchWriter):
    """BatchWriter implementation for FASTQ format.
    """
    def __init__(self, writer, batch_size):
        super(FastqWriter, self).__init__(writer, batch_size, 4)
    
    def _create_batch_list(self):
        return [None, None, '+', None] * self.batch_size
    
    def add_to_batch(self, name, sequence, qualities, batch, index):
        batch[index] = '@' + name
        batch[index+1] = sequence
        batch[index+3] = qualities

class FileWriter(object):
    """String writer that opens and writes to a pair of FIFOs.
    
    Args:
        fifo1: Path to the read1 FIFOs
        fifo2: Path to the read2 FIFOs
        kwargs: Additional arguments to pass to the ``open`` call.
    """
    def __init__(self, file1, file2, **kwargs):
        self.file1 = open(file1, 'wt', **kwargs)
        self.file2 = open(file2, 'wt', **kwargs)
    
    def __call__(self, read1_str, read2_str):
        self.file1.write(read1_str)
        self.file2.write(read2_str)
    
    def close(self):
        for f in (self.file1, self.file2):
            f.close()
