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
    def __init__(self, **kwargs):
        self.root = tempfile.mkdtemp(**kwargs)
    
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
