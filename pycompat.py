def popen(cmd, mode="r"):
    try:
        import subprocess
        return subprocess.Popen(cmd, shell=True, bufsize=bufsize, stdout=PIPE).stdout
    except ImportError:
        import os
        return os.popen(command, mode)

try:
    any = any
except NameError:
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False

try:
    set = set
except NameError:
    # Python 2.3
    from sets import Set as set
