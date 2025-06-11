import sys
from os import chdir
from os.path import abspath, dirname

selfdir = dirname(sys.argv[0])
if selfdir == "": selfdir = abspath(".")
chdir(selfdir)
