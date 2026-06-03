from core.blueprints.base_blueprint import BaseBlueprint

generator_bp = BaseBlueprint(
    "generator",
    __name__,
    template_folder="templates",
    static_folder="assets",
    static_url_path="/generator",
)