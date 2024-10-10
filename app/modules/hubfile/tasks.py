import logging
import os
import subprocess
from flamapy.metamodels.fm_metamodel.transformations import UVLReader, GlencoeWriter, SPLOTWriter
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat, DimacsWriter
import time

logger = logging.getLogger(__name__)


def transform_uvl(path, retries=5, delay=2):

    
    """
    Tries to process a UVL file. If the file does not exist, it retries
    `retries` times with a delay of `delay` seconds between each attempt.
    """
    attempt = 0
    while attempt < retries:
        if os.path.exists(path):
            break
        logger.info(f"File not found: {path}. Retrying... ({attempt + 1}/{retries})")
        attempt += 1
        time.sleep(delay)

    if not os.path.exists(path):
        logger.error(f"The file {path} was not found after {retries} attempts. Aborting transformation.")
        return
    

    logger.info(f"Processing UVL file at: {path}")

    try:
        fm = UVLReader(path).transform()
        logger.info("UVL file transformed successfully")
    except Exception as e:
        logger.error(f"Error transforming UVL file: {e}")

    # JSON Transformation
    json_path = path.replace(".uvl", ".json")
    try:
        GlencoeWriter(json_path, fm).transform()
        logger.info(f"JSON file created at: {json_path}")
    except Exception as e:
        logger.error(f"Error in JSON transformation: {e}")

    # CNF Transformation
    cnf_path = path.replace(".uvl", ".cnf")
    try:
        sat = FmToPysat(fm).transform()
        DimacsWriter(cnf_path, sat).transform()
        logger.info(f"CNF file created at: {cnf_path}")
    except Exception as e:
        logger.error(f"Error in CNF transformation: {e}")

    # SPLX Transformation
    splx_path = path.replace(".uvl", ".splx")
    try:
        SPLOTWriter(splx_path, fm).transform()
        logger.info(f"SPLX file created at: {splx_path}")
    except Exception as e:
        logger.error(f"Error in SPLX transformation: {e}")
