import logging
import os
import time

from flamapy.metamodels.fm_metamodel.transformations import GlencoeWriter, SPLOTWriter, UVLReader
from flamapy.metamodels.pysat_metamodel.transformations import DimacsWriter, FmToPysat

from app.features.flamapy.services import FlamapyService

logger = logging.getLogger(__name__)


def check_uvl(filepath: str):
    service = FlamapyService()
    return service.check_uvl(filepath)


def create_directory_if_not_exists(directory):
    """Create a directory if it does not exist yet."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Directory created: {directory}")


def transform_uvl(path, retries=5, delay=2):
    """Transform a UVL file into the Glencoe (JSON), SPLOT (SPLX) and DIMACS (CNF)
    formats. Retries a few times in case the file is not on disk yet."""
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
        return

    base_dir = os.path.dirname(os.path.dirname(path))

    glencoe_dir = os.path.join(base_dir, "glencoe")
    create_directory_if_not_exists(glencoe_dir)
    json_path = os.path.join(glencoe_dir, os.path.basename(path).replace(".uvl", ".json"))
    try:
        GlencoeWriter(json_path, fm).transform()
        logger.info(f"JSON file created at: {json_path}")
    except Exception as e:
        logger.error(f"Error in JSON transformation: {e}")

    splot_dir = os.path.join(base_dir, "splot")
    create_directory_if_not_exists(splot_dir)
    splx_path = os.path.join(splot_dir, os.path.basename(path).replace(".uvl", ".splx"))
    try:
        SPLOTWriter(splx_path, fm).transform()
        logger.info(f"SPLX file created at: {splx_path}")
    except Exception as e:
        logger.error(f"Error in SPLX transformation: {e}")

    dimacs_dir = os.path.join(base_dir, "dimacs")
    create_directory_if_not_exists(dimacs_dir)
    cnf_path = os.path.join(dimacs_dir, os.path.basename(path).replace(".uvl", ".cnf"))
    try:
        sat = FmToPysat(fm).transform()
        DimacsWriter(cnf_path, sat).transform()
        logger.info(f"CNF file created at: {cnf_path}")
    except Exception as e:
        logger.error(f"Error in CNF transformation: {e}")
