import init_logging as _

import random
import logging
import time
import sys
from tempfile import gettempdir
from os import mkdir, listdir
from shutil import rmtree

TEMP_DIR = None
THIS_ID = str(random.randint(0, 2 << 31))

def createTempDir():
    global TEMP_DIR
    
    if TEMP_DIR is not None: return TEMP_DIR
    
    temp_dir = f"{gettempdir().replace("\\", "/")}/qfppr_cctemp_{time.time()}_{THIS_ID}"
    logging.info(f"create temp dir: {temp_dir}")
    
    try: mkdir(temp_dir)
    except Exception as e: logging.warning(f"error when create temp dir: {e}")
    
    TEMP_DIR = temp_dir
    return temp_dir

def clearTempDir():
    if "--nocleartemp" in sys.argv:
        return
    
    for item in [
        f"{gettempdir()}/{item}"
        for item in listdir(gettempdir())
        if item.startswith("qfppr_cctemp_") and THIS_ID not in item
    ]:
        try:
            rmtree(item)
            logging.info(f"Remove Temp Dir: {item}")
        except Exception as e:
            logging.warning(e)
