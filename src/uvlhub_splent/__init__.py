import sys

from flask import render_template
from splent_framework.app_factory import create_splent_app
from splent_framework.configuration.configuration import get_app_version
from splent_framework.hooks.template_hooks import (
    register_template_hook,
    remove_template_hook,
)

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
    ("splent_io.splent_feature_autodeploy.hooks", "deployments_sidebar_item"),
]

# Lower renders first within a slot; features default to 100.
FIRST = 10
LAST = 900


def _feature_hook(module_name, func_name):
    """A hook function of a feature this product loaded, or None.

    Only features already imported count, since importing the hooks module
    of one the product does not use would register that feature's hooks.
    """
    return getattr(sys.modules.get(module_name), func_name, None)


def _place(slot, func, order):
    """Put func in slot at order, once, however often create_app runs."""
    remove_template_hook(slot, func)
    register_template_hook(slot, func, order=order)


def _remove_admin_sidebar_links():
    for module_name, func_name in ADMIN_SIDEBAR_LINKS:
        func = _feature_hook(module_name, func_name)
        if func is not None:
            remove_template_hook("layout.authenticated_sidebar", func)


def account_sidebar_heading():
    return render_template("hooks/account_sidebar_heading.html")


def team_sidebar_link():
    return render_template("hooks/sidebar_team.html")


def team_sections():
    """Every team role, in page order, with its published members.

    team's own list leaves out a role with nobody published under it.
    uvlhub's team page shows each organisation behind the project with
    its logo and description whether or not it lists people, as uvlhub
    always did.
    """
    from splent_framework.services.service_locator import service_proxy

    return [
        (
            role,
            sorted(
                (m for m in role.members if m.published),
                key=lambda m: (m.order, m.name),
            ),
        )
        for role in service_proxy("TeamService").roles()
    ]


def _arrange_menus():
    """uvlhub's menus, out of what the features put in them.

    The markup comes from the product's templates/hooks/, which take the
    place of the features' templates of the same name. This only decides
    which entries uvlhub shows and in which order.
    """
    auth = "splent_io.splent_feature_auth.hooks"
    signup = "splent_io.splent_feature_signup.hooks"

    # The signed-in sidebar ends with an Account section, the heading first,
    # then profile's Edit profile, then Log out. uvlhub's sidebar never had
    # a My account entry.
    my_account = _feature_hook(auth, "my_account_item")
    if my_account is not None:
        remove_template_hook("layout.authenticated_sidebar", my_account)
    logout = _feature_hook(auth, "logout_item")
    if logout is not None:
        remove_template_hook("layout.authenticated_sidebar", logout)
        _place("layout.sidebar.authenticated.items", logout, LAST)
    _place("layout.sidebar.authenticated.items", account_sidebar_heading, FIRST)

    # The user menu of the header lists Edit profile first and Log out last.
    navbar_logout = _feature_hook(auth, "navbar_authenticated")
    if navbar_logout is not None:
        _place("layout.navbar.authenticated", navbar_logout, LAST)

    # Visitors see only the login button in the header. Signing up is in the
    # sidebar, on the home page and under the login form, where "Don't have
    # an account?" comes before "Forgot your password?".
    signup_navbar = _feature_hook(signup, "signup_navbar")
    if signup_navbar is not None:
        remove_template_hook("layout.navbar.anonymous", signup_navbar)
    signup_footer = _feature_hook(signup, "signup_login_footer")
    if signup_footer is not None:
        _place("auth.login.form_footer", signup_footer, 50)

    # Team sits third at the top of the sidebar, after Explore (10) and
    # Dashboard (20) and before Generate models (40).
    if "splent_io.splent_feature_team" in sys.modules:
        _place("layout.sidebar.top", team_sidebar_link, 30)


def create_app(config_name=None):
    # No profile named: the framework follows SPLENT_ENV (dev, prod, test).
    app = create_splent_app(__name__, config_name)
    _remove_admin_sidebar_links()
    _arrange_menus()

    # The sidebar footer links the release, as in uvlhub. The prod image
    # writes .version from VERSION_TAG; in dev there is none and it hides.
    @app.context_processor
    def inject_app_version():
        return {"APP_VERSION": get_app_version()}

    # A callable, so the query only runs on the page that calls it.
    if "splent_io.splent_feature_team" in sys.modules:

        @app.context_processor
        def inject_team_sections():
            return {"team_sections": team_sections}

    return app
