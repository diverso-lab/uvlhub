import re
import sys

from flask import render_template
from flask_babel import lazy_gettext as _l
from splent_framework.app_factory import create_splent_app
from splent_framework.assets.asset_registry import register_asset
from splent_framework.configuration.configuration import get_app_version
from splent_framework.hooks import template_hooks
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


_HREF = re.compile(r'href="([^"]*)"')


def _field(obj, name):
    """An attribute of a menu entry or section, or its key when it is a dict."""
    return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)


def slot_beyond_menus(slot, sections):
    """What the hooks in ``slot`` draw, but for the entries already in the
    menu registry's ``sections``.

    A feature that registers its entry keeps its hook for a minor, and
    others have only the hook, so the administration is drawn from both
    (base_template.html): an entry whose every address the registry shows
    is left out. The markup is the hooks' own.
    """
    from markupsafe import Markup

    shown = {
        _field(entry, "url")
        for section in sections
        for entry in (_field(section, "entries") or ())
    } - {None, ""}
    drawn = []
    for hook in template_hooks.get_template_hooks(slot):
        html = hook() or ""
        addresses = set(_HREF.findall(html))
        if addresses and addresses <= shown:
            continue
        drawn.append(html)
    return Markup("\n".join(drawn))


def account_sidebar_heading():
    return render_template("hooks/account_sidebar_heading.html")


def home_get_started():
    """Sign up or sign in, for visitors."""
    from flask_login import current_user

    if not current_user.is_anonymous:
        return ""
    return render_template("hooks/home_get_started.html")


def home_about():
    """What uvlhub is and how to contribute."""
    return render_template("hooks/home_about.html")


def home_cite():
    """How to cite uvlhub."""
    return render_template("hooks/home_cite.html")


def _fill_the_home(app):
    """uvlhub's cards beside the top datasets, in public's home.aside slot.

    In uvlhub.io's order: Let's get started! first, for visitors, then what
    the features put there (statistics' counters), then what uvlhub is and
    how to cite it. public draws the home in two columns once home.aside has
    something, with a stylesheet of its own for the public shell; the home
    is drawn in the app shell (SPLENT_SHELL_PUBLIC), so that stylesheet
    serves the app shell as well.
    """
    if "public.index" not in app.view_functions:
        return
    _place("home.aside", home_get_started, FIRST)
    _place("home.aside", home_about, LAST)
    _place("home.aside", home_cite, LAST + 10)
    register_asset(
        "css", "public.assets", order=100, shell="app", subfolder="css", filename="home.css"
    )


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


def _skin_the_public_shell():
    """uvlhub.io's error card on theme's public shell.

    In uvlhub that shell, public_base.html, only draws theme's 404: the
    public pages are in the app shell (SPLENT_SHELL_PUBLIC). The product
    dresses it as uvlhub.io's card with its own stylesheet, the one its 400,
    401 and 500 pages wear. Registered after the features, as a skin is,
    so it comes after theirs."""
    register_asset("css", "static", order=200, filename="css/uvlhub-error.css")


def create_app(config_name=None):
    # No profile named: the framework follows SPLENT_ENV (dev, prod, test).
    app = create_splent_app(__name__, config_name)
    _arrange_menus()
    _bridge_menus()
    _fill_the_home(app)

    # /api/me of uvlhub 2.12, until legacy_urls (CO-2) answers it.
    if "profile.my_profile" in app.view_functions:
        app.register_blueprint(aliases_bp)

    _skin_the_public_shell()

    @app.context_processor
    def inject_slot_beyond_menus():
        return {"slot_beyond_menus": slot_beyond_menus}

    # The sidebar footer links the release, as in uvlhub. The prod image
    # writes .version from VERSION_TAG; in dev there is none and it hides.
    @app.context_processor
    def inject_app_version():
        return {"APP_VERSION": get_app_version()}

    return app
