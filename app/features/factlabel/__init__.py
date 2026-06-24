from splent_framework.blueprints.base_blueprint import BaseBlueprint

factlabel_bp = BaseBlueprint("factlabel", __name__, template_folder="templates")


def init_feature(app):
    # The FactLabel URL is a UVL-domain concern; expose it to templates without
    # the generic hubfile model knowing about it.
    from app.features.factlabel.services import FactlabelService

    app.add_template_global(FactlabelService.external_url, name="factlabel_url")
