def popen(cmd, mode="r"):
    try:
        import subprocess
        return subprocess.Popen(cmd, shell=True, bufsize=bufsize, stdout=PIPE).stdout
    except ImportError:
        import os
        return os.popen(command, mode)

try:
    any([])
except NameError:
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False

