import logging
from flamapy.metamodels.fm_metamodel.transformations import UVLReader, GlencoeWriter, SPLOTWriter
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat, DimacsWriter

logger = logging.getLogger(__name__)

def process_event_worker(path):
    logger.info(f"Processing UVL file at: {path}")

    try:
        fm = UVLReader(path).transform()
        logger.info(f"UVL file transformed successfully")
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
