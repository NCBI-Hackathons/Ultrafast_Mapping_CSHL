from contextlib import contextmanager
import os
import re
import shutil
import sys
import tempfile

@contextmanager
def open_(path, mode, **kwargs):
    """Open a file without worrying whether it's an actual path or '-' (for
    stdin/stdout)."""
    if path == '-':
        if 'r' in mode:
            yield sys.stdin
        elif 'w' in mode:
            yield sys.stdout
    else:
        with open(path, mode, **kwargs) as f:
            yield f

class TempDir(object):
    """Context manager that creates a temporary directory and cleans it up
    upon exit.
    """
    def __init__(self, **kwargs):
        self.root = os.path.abspath(tempfile.mkdtemp(**kwargs))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
    
    def close(self):
        shutil.rmtree(self.root)
    
    def make_path(self, relative_path):
        return os.path.join(self.root, relative_path)
    
    def mkfifos(self, *names, subdir=None, **kwargs):
        parent = self.root
        if subdir:
            parent = os.path.join(parent, subdir)
            os.makedirs(parent, exist_ok=True)
        fifo_paths = [os.path.join(parent, name) for name in names]
        for path in fifo_paths:
            os.mkfifo(path, **kwargs)
        return fifo_paths

def wrap_progress(iterable, **kwargs):
    """Wrap an iterable in a tqdm progress bar, if the library is installed.
    """
    try:
        import tqdm
        return tqdm.tqdm(iterable, **kwargs)
    except:
        return iterable

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
