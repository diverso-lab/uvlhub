import sys

from flask import render_template
from flask_babel import lazy_gettext as _l
from splent_framework.app_factory import create_splent_app
from splent_framework.configuration.configuration import get_app_version
from splent_framework.hooks.template_hooks import (
    register_template_hook,
    remove_template_hook,
)
from splent_framework.nav.menu_registry import (
    ANONYMOUS,
    get_menu_items,
    get_menu_sections,
    get_user_menu_items,
    register_menu_item,
    register_menu_section,
    register_user_menu_item,
)

from uvlhub_splent.aliases import aliases_bp

# Lower renders first within a slot; features default to 100.
FIRST = 10
LAST = 900

# Entries of uvlhub's menus whose feature, at the version the product pins,
# still draws them as markup in a slot the shell cannot bring to uvlhub's
# look: the monolith's theme markup (explore, statistics and dataset in the
# sidebar), or a menu of its own (profile's name and auth's Log out in the
# header, auth's Log in link for visitors). The shell draws a section from
# the menu registry once it has entries there, and generator's Generate
# models already is in "site", so Explore, Dashboard and Team have to be
# there as well or the sidebar loses them.
#
# The developer entries are bridged for another reason. apikeys draws its
# own and, inside it, apidocs' in layout.authenticated_sidebar, the slot the
# main and admin sections share, which the shell leaves out as soon as
# either has registry entries: an admin entry from any feature's next
# release would take the Developer section away. Registered, they no longer
# depend on what the other features have migrated, and the slot keeps the
# administration's entries only, which the shell heads as the registry
# does (base_template.html).
#
# Each is registered with the key, the endpoint and the icon its feature's
# next release registers (its working copy does), under the label it shows
# today, and its hook, when it has one in a slot, leaves the slot. A feature
# that registers the endpoint itself has moved on and is left alone, so each
# bridge retires with the release of its feature.
SIDEBAR_BRIDGES = [
    dict(
        key="explore",
        label=_l("Explore"),
        endpoint="explore.index",
        icon="search",
        section="site",
        order=10,
        hook=("splent_io.splent_feature_explore.hooks", "explore_sidebar_link"),
        slot="layout.sidebar.top",
    ),
    dict(
        key="statistics",
        label=_l("Dashboard"),
        endpoint="statistics.index",
        icon="bar-chart-2",
        section="site",
        order=20,
        hook=("splent_io.splent_feature_statistics.hooks", "dashboard_sidebar_link"),
        slot="layout.sidebar.top",
    ),
    # Third, after Explore (10) and Dashboard (20) and before Generate
    # models (40). team's own entry comes at 50: once it is pinned, the
    # product puts it back here with [tool.splent.layout.menu] order.
    dict(
        key="team",
        label=_l("Team"),
        endpoint="team.index",
        icon="users",
        section="site",
        order=30,
        match=("team.index", "team.detail"),
    ),
    dict(
        key="dataset_upload",
        label=_l("Upload dataset"),
        endpoint="dataset.create_dataset",
        icon="upload",
        section="datasets",
        order=10,
        match=("dataset.create_dataset", "dataset.import_dataset"),
        hook=("splent_io.splent_feature_dataset.hooks", "sidebar_datasets"),
        slot="layout.authenticated_sidebar",
    ),
    dict(
        key="dataset_list",
        label=_l("My datasets"),
        endpoint="dataset.list_dataset",
        icon="folder",
        section="datasets",
        order=20,
        match=("dataset.list_dataset", "dataset.edit_metadata"),
    ),
    # uvlhub.io's order: the docs, the tokens, a new token.
    dict(
        key="apidocs",
        label=_l("Read the API docs"),
        endpoint="flasgger.apidocs",
        icon="book-open",
        section="developer",
        order=10,
        external=True,
        hook=("splent_io.splent_feature_apidocs.hooks", "developer_link"),
        slot="apikeys.sidebar.developer",
    ),
    dict(
        key="apikeys",
        label=_l("API tokens"),
        endpoint="apikeys.index",
        icon="key",
        section="developer",
        order=20,
        match="apikeys.",
        hook=("splent_io.splent_feature_apikeys.hooks", "apikeys_sidebar_item"),
        slot="layout.authenticated_sidebar",
    ),
    dict(
        key="apikeys_new",
        label=_l("New API token"),
        endpoint="apikeys.new",
        icon="plus-circle",
        section="developer",
        order=30,
    ),
]

# The section dataset declares for its entries, while it does not.
DATASETS_SECTION = dict(key="datasets", label=_l("Datasets"), order=110)

USER_MENU_BRIDGES = [
    # Visitors: the login button of the header, instead of auth's text link.
    dict(
        key="user_login",
        label=_l("Log in"),
        endpoint="auth.login",
        icon="log-in",
        section="anonymous",
        order=10,
    ),
    dict(
        key="user_profile",
        label=_l("Edit profile"),
        endpoint="profile.edit_profile",
        icon="user",
        section="account",
        order=10,
    ),
    dict(
        key="user_logout",
        label=_l("Log out"),
        endpoint="auth.logout",
        icon="log-out",
        section="account",
        order=900,
    ),
]


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


def account_sidebar_heading():
    return render_template("hooks/account_sidebar_heading.html")


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

    The markup is the features' own, but for the Account heading, which the
    product draws from its templates/hooks/. This only decides which entries
    uvlhub shows and in which order, for the sections the shell still draws
    from the slots (see base_template.html).
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

    # Visitors see only the login button in the header. Signing up is in the
    # sidebar, on the home page and under the login form, where "Don't have
    # an account?" comes before "Forgot your password?".
    signup_navbar = _feature_hook(signup, "signup_navbar")
    if signup_navbar is not None:
        remove_template_hook("layout.navbar.anonymous", signup_navbar)
    signup_footer = _feature_hook(signup, "signup_login_footer")
    if signup_footer is not None:
        _place("auth.login.form_footer", signup_footer, 50)


def _bridge_menus():
    """Register what SIDEBAR_BRIDGES and USER_MENU_BRIDGES name, while the
    features that own those entries do not register them themselves."""
    # "Let's get started!", as uvlhub.io heads the visitors' part, instead of
    # the registry's "Get started"; the same place and audience.
    for section in get_menu_sections():
        if section.key == "anonymous":
            register_menu_section(
                "anonymous", _l("Let's get started!"), section.order, audience=ANONYMOUS
            )

    registered = {item.endpoint for item in get_menu_items() if item.endpoint}
    for bridge in SIDEBAR_BRIDGES:
        entry = dict(bridge)
        hook, slot = entry.pop("hook", None), entry.pop("slot", None)
        if entry["endpoint"] in registered:
            continue
        sections = {known.key for known in get_menu_sections()}
        if (
            entry["section"] == DATASETS_SECTION["key"]
            and entry["section"] not in sections
        ):
            register_menu_section(**DATASETS_SECTION)
        register_menu_item(**entry)
        func = _feature_hook(*hook) if hook else None
        if func is not None:
            remove_template_hook(slot, func)

    registered = {item.endpoint for item in get_user_menu_items() if item.endpoint}
    for entry in USER_MENU_BRIDGES:
        if entry["endpoint"] not in registered:
            register_user_menu_item(**entry)


def _answer_not_found(app):
    """Answer an address that leads nowhere with uvlhub's page, the card of
    uvlhub.io (errors.handle_404, 404.html).

    The framework registers errors.py's handler, and theme replaces it as
    it starts with one that renders its errors/404.html in the public
    shell. Registered again here, after the features, the product's own
    page answers, and theme's template stays theme's for the products that
    draw it. A page that cannot be drawn gets Werkzeug's plain answer, as
    the framework's handlers give."""
    from uvlhub_splent import errors

    def not_found(e):
        try:
            return errors.handle_404(app, e)
        except Exception:
            app.logger.exception("The 404 page could not be drawn")
            return e.get_response()

    app.register_error_handler(404, not_found)


def create_app(config_name=None):
    # No profile named: the framework follows SPLENT_ENV (dev, prod, test).
    app = create_splent_app(__name__, config_name)
    _arrange_menus()
    _bridge_menus()

    # /api/me of uvlhub 2.12, until legacy_urls (CO-2) answers it.
    if "profile.my_profile" in app.view_functions:
        app.register_blueprint(aliases_bp)

    _answer_not_found(app)

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
