import json
import logging

from app import create_app, db
from app.features.factlabel.models import FactLabel
from app.features.factlabel.services import FactlabelService
from app.features.hubfile.models import Hubfile

logger = logging.getLogger(__name__)

app = create_app()


def compute_factlabel(hubfile_id: int, light_fact_label: bool = False):
    logger.info(f"[FACTLABEL] Worker DB URL: {db.engine.url}")
    logger.info(f"[FACTLABEL] Starting computation for Hubfile {hubfile_id} (light={light_fact_label})")

    with app.app_context():
        try:
            hubfile = db.session.get(Hubfile, hubfile_id)
            if not hubfile:
                logger.warning(f"[FACTLABEL] Hubfile {hubfile_id} not found")
                return

            content = FactlabelService().get_characterization(hubfile, light_fact_label=light_fact_label)
            factlabel = db.session.get(FactLabel, hubfile_id) or FactLabel(hubfile_id=hubfile_id)
            factlabel.factlabel_json = json.dumps(content)

            db.session.add(factlabel)
            db.session.commit()
            logger.info(f"[FACTLABEL] FactLabel computed and stored for Hubfile {hubfile_id}")

            # Materialise typed metrics for the dashboard. Only the full
            # (non-light) run carries the complete semantic analysis, so we
            # don't overwrite a richer row with a sparser light one.
            if not light_fact_label:
                from app.features.factlabel.metrics_sync import upsert_metrics_from_payload

                try:
                    upsert_metrics_from_payload(hubfile_id, content)
                    logger.info(f"[FACTLABEL] Metrics row upserted for Hubfile {hubfile_id}")
                except Exception:
                    # Metrics extraction failures must not poison the fact label
                    # itself; the row is recoverable via backfill.
                    logger.exception(f"[FACTLABEL] Metrics upsert failed for Hubfile {hubfile_id}")
        except Exception as e:
            logger.exception(f"[FACTLABEL] Error computing FactLabel for Hubfile {hubfile_id}: {e}")
            db.session.rollback()
