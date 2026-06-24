from splent_framework.blueprints.base_blueprint import BaseBlueprint

flamapy_bp = BaseBlueprint("flamapy", __name__, template_folder="templates")


def init_feature(app):
    # The Flamapy IDE URL is a UVL-domain concern; expose it to templates without
    # the generic hubfile model knowing about it.
    from app.features.flamapy.services import FlamapyService

    app.add_template_global(FlamapyService.ide_url, name="ide_url")
