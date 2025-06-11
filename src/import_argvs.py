import fix_workpath as _
import init_logging as _

import json
import logging
import sys
from os.path import exists, isfile

ARGVFILE = "./default-argvs.json"

if exists(ARGVFILE) and isfile(ARGVFILE):
    logging.info(f"Loading default argvs from {ARGVFILE}")
    
    try:
        with open(ARGVFILE, "r", encoding="utf-8") as f:
            sys.argv.extend(json.load(f))
    except Exception as e:
        logging.error(f"Failed to load default argvs from {ARGVFILE}: {repr(e)}")
