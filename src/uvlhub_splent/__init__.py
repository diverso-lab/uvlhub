import sys

from splent_framework.app_factory import create_splent_app
from splent_framework.configuration.configuration import get_app_version
from splent_framework.hooks.template_hooks import remove_template_hook

# Admin entries the SPLENT features add to the signed-in sidebar. uvlhub's
# sidebar has no admin section (Datasets, Developer and Account only), so the
# product drops them; their pages stay reachable under /admin.
ADMIN_SIDEBAR_LINKS = [
    ("splent_io.splent_feature_admin.hooks", "admin_sidebar_link"),
    ("splent_io.splent_feature_auth.hooks", "users_item"),
    ("splent_io.splent_feature_mailhog.hooks", "mailhog_sidebar_link"),
    ("splent_io.splent_feature_nginx.hooks", "nginx_sidebar_link"),
    ("splent_io.splent_feature_phpmyadmin.hooks", "phpmyadmin_sidebar_link"),
    ("splent_io.splent_feature_settings.hooks", "settings_admin_link"),
    ("splent_io.splent_feature_theme.hooks", "appearance_admin_link"),
    ("splent_io.splent_feature_theme.hooks", "menus_admin_link"),
    ("splent_io.splent_feature_legal.hooks", "legal_admin_link"),
    ("splent_io.splent_feature_recaptcha.hooks", "recaptcha_admin_link"),
    ("splent_io.splent_feature_media.hooks", "media_admin_link"),
    ("splent_io.splent_feature_team.hooks", "team_admin_link"),
    ("splent_io.splent_feature_partners.hooks", "partners_admin_link"),
]


def _remove_admin_sidebar_links():
    for module_name, func_name in ADMIN_SIDEBAR_LINKS:
        # Only features this product loaded: importing the hooks module of
        # one it does not use would register that feature's hooks.
        module = sys.modules.get(module_name)
        func = getattr(module, func_name, None)
        if func is None:
            continue
        remove_template_hook("layout.authenticated_sidebar", func)


def create_app(config_name=None):
    # No profile named: the framework follows SPLENT_ENV (dev, prod, test).
    app = create_splent_app(__name__, config_name)
    _remove_admin_sidebar_links()

    # The sidebar footer links the release, as in uvlhub. The prod image
    # writes .version from VERSION_TAG; in dev there is none and it hides.
    @app.context_processor
    def inject_app_version():
        return {"APP_VERSION": get_app_version()}

    return app
