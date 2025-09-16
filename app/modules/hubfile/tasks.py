import json
import logging
import os
import time

from flamapy.metamodels.fm_metamodel.transformations import GlencoeWriter, SPLOTWriter, UVLReader
from flamapy.metamodels.pysat_metamodel.transformations import DimacsWriter, FmToPysat
from sqlalchemy.orm import sessionmaker

from app import create_app, db
from app.modules.factlabel.services import FactlabelService
from app.modules.hubfile.models import Hubfile

logger = logging.getLogger(__name__)


def create_directory_if_not_exists(directory):
    """Helper function to create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Directory created: {directory}")


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

    # Get the base directory (dataset folder) and ensure it's not the uvl folder
    base_dir = os.path.dirname(os.path.dirname(path))

    # Glencoe JSON Transformation
    glencoe_dir = os.path.join(base_dir, "glencoe")
    create_directory_if_not_exists(glencoe_dir)
    json_path = os.path.join(glencoe_dir, os.path.basename(path).replace(".uvl", ".json"))
    try:
        GlencoeWriter(json_path, fm).transform()
        logger.info(f"JSON file created at: {json_path}")
    except Exception as e:
        logger.error(f"Error in JSON transformation: {e}")

    # SPLOT SPLX Transformation
    splot_dir = os.path.join(base_dir, "splot")
    create_directory_if_not_exists(splot_dir)
    splx_path = os.path.join(splot_dir, os.path.basename(path).replace(".uvl", ".splx"))
    try:
        SPLOTWriter(splx_path, fm).transform()
        logger.info(f"SPLX file created at: {splx_path}")
    except Exception as e:
        logger.error(f"Error in SPLX transformation: {e}")

    # DIMACS CNF Transformation
    dimacs_dir = os.path.join(base_dir, "dimacs")
    create_directory_if_not_exists(dimacs_dir)
    cnf_path = os.path.join(dimacs_dir, os.path.basename(path).replace(".uvl", ".cnf"))
    try:
        sat = FmToPysat(fm).transform()
        DimacsWriter(cnf_path, sat).transform()
        logger.info(f"CNF file created at: {cnf_path}")
    except Exception as e:
        logger.error(f"Error in CNF transformation: {e}")


app = create_app()
SessionLocal = sessionmaker(bind=db.engine)


def compute_factlabel(hubfile_id: int):
    logger.info(f"[FACTLABEL] Worker DB URL: {db.engine.url}")
    logger.info(f"[FACTLABEL] Starting computation for Hubfile {hubfile_id}")

    with app.app_context():
        session = SessionLocal()
        try:
            hubfile = session.get(Hubfile, hubfile_id)
            if not hubfile:
                logger.warning(f"[FACTLABEL] Hubfile {hubfile_id} not found")
                return

            # 👉 Generar caracterización real
            content = FactlabelService().get_characterization(hubfile)

            # Guardar como string JSON (porque factlabel_json es Text)
            hubfile.factlabel_json = json.dumps(content)

            session.add(hubfile)
            session.commit()

            logger.info(f"[FACTLABEL] ✅ FactLabel computed and stored for Hubfile {hubfile_id}")
        except Exception as e:
            logger.exception(f"[FACTLABEL] Error computing FactLabel for Hubfile {hubfile_id}: {e}")
            session.rollback()
        finally:
            session.close()
