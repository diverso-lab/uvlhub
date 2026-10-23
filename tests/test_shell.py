"""uvlhub's application shell, base_template.html (SH-1, P1 of stage 1).

The pages a visitor, a user and an administrator open first answer, and
every stylesheet, script and icon they link on this site is there: the
Metronic shell linked six scripts that answered 404. No page asks another
site for anything (Google Analytics, feather from unpkg, Google Fonts), and
nothing of Metronic is left in the product's templates, in its static
folder or in what the shell draws.

The sidebar and the account menu are drawn from the menu registry section
by section, and from the slots the features fill where the registry has
nothing: never both, so no entry shows twice. Until their minors are
pinned, the product registers the entries whose feature still draws them
as Metronic markup (explore, statistics, dataset) or as a menu of its own
(profile, auth in the header), and the developer entries, which apikeys
draws in the slot the admin section shares. Those features still draw
Metronic in the header and on their pages (explore, dataset), so the check
of the rendered pages leaves out what they draw, and METRONIC_UNTIL_P2 goes
once P2 pins them.

The chrome draws its icons from a sprite of its own (Phosphor), and the
page asks for Inter from the product: both are checked to be there.

It starts from an empty test database with two accounts, so run it under
the test lock:

    docker exec -u splent splent_cli_container bash -lc \
        'cd /workspace && flock /tmp/splent-test.lock splent product:test --own-tests'
"""

import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from pathlib import Path

import pytest
from splent_framework.db import db
from splent_framework.fixtures.fixtures import _reset_db
from splent_framework.hooks import template_hooks

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "uvlhub_splent"
STATIC = PACKAGE / "static"
TEMPLATES = PACKAGE / "templates"

PASSWORD = "1234"
ACCOUNTS = {
    "user": ("user1@example.com", "user"),
    "admin": ("admin@example.com", "admin"),
}
BROWSERS = ["anonymous", *ACCOUNTS]
PAGES = ["/", "/login", "/signup/", "/explore", "/team", "/datasets/list"]
# The page the checks of the shell itself open: one every pinned feature
# draws in the app shell.
SHELL_PAGE = "/explore"
# The pages the features write for the public site, which uvlhub draws in
# the app shell through SPLENT_SHELL_PUBLIC, and the template of each.
PUBLIC_PAGES = {"/": "public/index.html", "/team": "team/list.html"}

# Keenthemes' names, as the CLI's check:vendor looks for them in a tree.
KEENTHEMES = re.compile(
    r"KTUtil|KTComponents|KTApp|KTMenu|KTStepper|keenthemes|Metronic"
    r"|ki-duotone|ki-outline|ki-solid|data-kt-"
)
# Metronic's element ids (kt_app_body, kt_app_sidebar...) in a page. Not in
# the static files, where month names such as "okt_nov" would match.
KT_ID = re.compile(r"(?<![\w-])kt_")
THIRD_PARTY = (
    "googletagmanager",
    "unpkg.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
)
# The static files read as text.
TEXT_FILES = {".css", ".js", ".html", ".svg", ".json", ".txt", ".md"}

METRONIC_UNTIL_P2 = {"explore", "statistics", "generator", "dataset"}
# The pages whose content one of those features draws.
PAGES_OF_METRONIC_FEATURES = {"/explore", "/datasets/list"}

# Bundles the shell links that answer 404 in dev, because nobody has built
# them yet in the cache of the pinned release (profile 1.6.0, reset 1.5.0).
# A bundle under dist/ is there once its feature's assets are built
# (splent feature:compile, the image build), which the product does not do.
# Each goes once it is built in dev; any other bundle missing is a failure.
UNBUILT_BUNDLES = {
    "/profile/dist/profile.bundle.js",
    "/reset/dist/reset.bundle.js",
}


class _Assets(HTMLParser):
    """The addresses of the <link href> and <script src> of a page."""

    def __init__(self):
        super().__init__()
        self.found = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        address = attrs.get("href") if tag == "link" else attrs.get("src")
        if tag in ("link", "script") and address:
            self.found.append(address)


def _assets_on_this_site(html):
    parser = _Assets()
    parser.feed(html)
    return [a for a in parser.found if a.startswith("/") and not a.startswith("//")]


class _Sidebar(HTMLParser):
    """What the sidebar of a page draws: its headings and the address of
    each entry, in order."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.headings = []
        self.links = []
        self._in_heading = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "aside" and attrs.get("id") == "sidebar":
            self.depth = 1
        elif self.depth:
            if tag == "aside":
                self.depth += 1
            if tag == "li" and "sidebar-header" in (attrs.get("class") or "").split():
                self._in_heading = True
                self.headings.append("")
            if tag == "a" and "sidebar-link" in (attrs.get("class") or "").split():
                self.links.append(attrs.get("href"))

    def handle_endtag(self, tag):
        if self.depth and tag == "aside":
            self.depth -= 1
        if tag == "li":
            self._in_heading = False

    def handle_data(self, data):
        if self._in_heading and data.strip():
            self.headings[-1] = (self.headings[-1] + " " + data.strip()).strip()


def _sidebar(html):
    parser = _Sidebar()
    parser.feed(html)
    return parser


def _feature_of(func):
    """The feature a template hook belongs to, as "dataset", or ""."""
    parts = (getattr(func, "__module__", None) or "").split(".")
    if len(parts) > 1 and parts[0] == "splent_io":
        return parts[1].removeprefix("splent_feature_")
    return ""


@pytest.fixture(scope="module")
def browsers(app):
    """A browser for nobody, one signed in as a user and one as an
    administrator, on a test database with just their two accounts."""
    from splent_io.splent_feature_auth.models import User

    # Only for the setup. A request opens an app context of its own unless
    # one is open already, and Flask-Login keeps the account it served in
    # that context's g, so a context held open for the module would hand
    # the administrator's account to the anonymous browser.
    with app.app_context():
        _reset_db()
        for email, role in ACCOUNTS.values():
            db.session.add(User(email=email, password=PASSWORD, role=role, active=True))
        db.session.commit()

    opened = {"anonymous": app.test_client()}
    for name, (email, _role) in ACCOUNTS.items():
        browser = app.test_client()
        response = browser.post("/login", data={"email": email, "password": PASSWORD})
        assert response.status_code == 302, f"{email} could not sign in"
        opened[name] = browser
    return opened


@pytest.fixture
def without_metronic_features(app, monkeypatch):
    """The template slots without what METRONIC_UNTIL_P2 put in them."""
    every_hook = template_hooks.get_template_hooks

    def hooks(name):
        return [f for f in every_hook(name) if _feature_of(f) not in METRONIC_UNTIL_P2]

    # render_template_hooks reads the module's function, a template the global.
    monkeypatch.setattr(template_hooks, "get_template_hooks", hooks)
    monkeypatch.setitem(app.jinja_env.globals, "get_template_hooks", hooks)


def _until_the_shell_is_public(app, page):
    """Expect ``page`` out of uvlhub's shell while its feature's template
    names theme's public_base.html instead of shell('public').

    public 1.9.0 and team 0.6.0 do, so SPLENT_SHELL_PUBLIC cannot bring the
    home and /team into the app shell. Their next releases draw
    shell('public') (their working copies do, and so do these pages under
    SPLENT_FEATURE_SOURCES); this goes once those releases are pinned.
    """
    template = PUBLIC_PAGES.get(page)
    if template is None:
        return
    source = app.jinja_env.loader.get_source(app.jinja_env, template)[0]
    if 'extends "public_base.html"' in source:
        pytest.xfail(f"{template} still extends public_base.html by name")


def _open_in_the_shell(app, browsers, who, page):
    """``page`` as ``who`` gets it, where it lands (the forms send an
    account home), expected in the app shell unless that is a public page
    its feature still draws in theme's public_base.html."""
    response = browsers[who].get(page, follow_redirects=True)
    assert response.status_code == 200, (
        f"{page} answered {who} with {response.status_code}"
    )
    _until_the_shell_is_public(app, response.request.path)
    return response.get_data(as_text=True)


def _open(browsers, who, page):
    response = browsers[who].get(page, follow_redirects=True)
    status = response.status_code
    assert status == 200, f"{page} answered {who} with {status}"
    return response.get_data(as_text=True)


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("who", BROWSERS)
def test_a_page_answers_in_the_shell(app, browsers, who, page):
    html = _open_in_the_shell(app, browsers, who, page)

    assert '<aside id="sidebar" class="uvl-sidebar"' in html
    # The page's own heading or, when it draws none, its title.
    assert html.count("<h1") == 1
    # The signed-in browsers really are: their sidebar ends with Log out.
    assert ('href="/logout"' in html) == (who != "anonymous")


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("who", BROWSERS)
def test_the_sidebar_shows_each_entry_once(app, browsers, who, page):
    links = _sidebar(_open_in_the_shell(app, browsers, who, page)).links

    assert links
    assert len(links) == len(set(links))


@pytest.mark.parametrize("who", BROWSERS)
def test_the_home_is_publics_with_uvlhubs_cards_beside_it(app, browsers, who):
    """public's own home in the app shell: its two columns, the top datasets
    and, beside them, the product's cards around what the features put
    there, in uvlhub.io's order. The site's title heads it, in the band."""
    _until_the_shell_is_public(app, "/")
    html = _open(browsers, who, "/")
    aside = html[html.index('<aside class="home-columns__aside">') :]

    # Beside the top datasets, or alone on a hub with none yet.
    assert '<div class="container home-columns' in html
    assert "/public/css/home.css" in html
    assert ("get started!</h2>" in aside) == (who == "anonymous")
    assert aside.index("Hub statistics") < aside.index("What is uvlhub.io?")
    assert aside.index("What is uvlhub.io?") < aside.index("Cite us!")
    assert '<h1 class="uvl-page-title">uvlhub — ' in html
    assert not (TEMPLATES / "public" / "index.html").exists()


def test_the_team_is_teams_page_under_the_trail(app, browsers, monkeypatch):
    """team's own list in the app shell, headed by its name without the
    site's ("Team — uvlhub_splent" in its title block), under the trail theme
    derives for it with uvlhub's SITE_BREADCRUMBS."""
    _until_the_shell_is_public(app, "/team")
    monkeypatch.setitem(app.config, "SITE_BREADCRUMBS", "all")
    html = _open(browsers, "anonymous", "/team")
    trail = html[html.index('<ol class="breadcrumb">') :]
    trail = trail[: trail.index("</ol>")]

    assert '<h1 class="uvl-page-title">Team</h1>' in html
    assert '<a href="/">Home</a>' in trail
    assert '<li class="breadcrumb-item active" aria-current="page">Team</li>' in trail
    assert not (TEMPLATES / "team" / "list.html").exists()


@pytest.mark.parametrize("who", BROWSERS)
def test_the_sidebar_is_uvlhubs(browsers, who):
    sidebar = _sidebar(_open(browsers, who, SHELL_PAGE))
    paths = [urlsplit(link).path for link in sidebar.links]

    # The site's own entries first, for everyone, in uvlhub.io's order.
    assert paths[:4] == ["/explore", "/statistics", "/team", "/generator/"]
    if who == "anonymous":
        assert sidebar.headings == ["Let's get started!"]
        assert "/login" in paths and "/signup/" in paths
    elif who == "user":
        assert sidebar.headings == ["Datasets", "Developer", "Account"]
        assert paths[4:6] == ["/datasets/upload", "/datasets/list"]
        # uvlhub.io's Developer: the docs, the tokens, a new token.
        assert paths[6:9] == ["/apidocs/", "/developer/tokens", "/developer/tokens/new"]
        assert paths[-1] == "/logout"
    else:
        # The administration, for the accounts it lets in (decision D-admin),
        # where the registry puts its section: after Datasets.
        assert sidebar.headings == [
            "Datasets",
            "Administration",
            "Developer",
            "Account",
        ]
        assert paths[4:6] == ["/datasets/upload", "/datasets/list"]
        docs = paths.index("/apidocs/")
        assert paths[docs : docs + 3] == [
            "/apidocs/",
            "/developer/tokens",
            "/developer/tokens/new",
        ]
        assert paths[-1] == "/logout"


@pytest.mark.parametrize("who", ACCOUNTS)
def test_the_administration_is_offered_to_the_accounts_it_lets_in(browsers, who):
    """The panels the features add (settings, theme's Appearance...) are in
    the sidebar of an administrator, between Datasets and Developer, and in
    nobody else's."""
    paths = [
        urlsplit(link).path for link in _sidebar(_open(browsers, who, SHELL_PAGE)).links
    ]
    panels = [p for p in paths if p.startswith("/admin/")]

    if who == "admin":
        assert {"/admin/settings", "/admin/appearance"} <= set(panels)
        assert paths.index("/datasets/list") < paths.index("/admin/settings")
        assert paths.index("/admin/settings") < paths.index("/apidocs/")
    else:
        assert panels == []


@pytest.mark.parametrize("who", ACCOUNTS)
def test_the_account_menu_names_the_account_and_its_entries(browsers, who):
    html = _open(browsers, who, SHELL_PAGE)
    menu = html[html.index('class="dropdown-menu dropdown-menu-end uvl-user-menu"') :]
    menu = menu[: menu.index("</li>")]

    assert ACCOUNTS[who][0] in menu
    assert 'href="/profile/edit"' in menu
    assert 'href="/logout"' in menu
    # Drawn from the registry, so the features' own account menu is not.
    assert html.count('href="/logout"') == 2  # the sidebar's and this one


def test_a_section_with_registry_entries_does_not_draw_its_slot(
    app, browsers, monkeypatch
):
    """The visitors' section from the registry: auth's and signup's slot
    entries are left out, so nothing shows twice."""
    registered = [
        {
            "key": "anonymous",
            "label": "Registered heading",
            "entries": [
                {
                    "key": "only_entry",
                    "label": "Only entry",
                    "url": "/only-entry",
                    "icon": "log-in",
                    "active": False,
                    "aria_current": None,
                    "badge": None,
                    "section": "anonymous",
                    "external": False,
                }
            ],
        }
    ]
    every_section = app.jinja_env.globals["menu_sections"]

    def sections():
        return every_section() + registered

    monkeypatch.setitem(app.jinja_env.globals, "menu_sections", sections)
    sidebar = _sidebar(_open(browsers, "anonymous", SHELL_PAGE))

    assert "Registered heading" in sidebar.headings
    assert "Let's get started!" not in sidebar.headings
    assert "/only-entry" in sidebar.links
    assert "/login" not in sidebar.links


def test_an_admin_section_in_the_registry_leaves_the_developer_section(
    app, browsers, monkeypatch
):
    """The main, admin and developer sections share one slot, left out as
    soon as one of them has registry entries. An administration entry a
    feature registers (auth's Users, theme's Appearance...) must not take
    the Developer section with it."""
    registered = [
        {
            "key": "admin",
            "label": "Administration",
            "entries": [
                {
                    "key": "users",
                    "label": "Users",
                    "url": "/admin/users",
                    "icon": "users",
                    "active": False,
                    "aria_current": None,
                    "badge": None,
                    "section": "admin",
                    "external": False,
                }
            ],
        }
    ]
    every_section = app.jinja_env.globals["menu_sections"]

    def sections():
        # This one in place of the admin entries the features register.
        return [
            section for section in every_section() if section["key"] != "admin"
        ] + registered

    monkeypatch.setitem(app.jinja_env.globals, "menu_sections", sections)
    sidebar = _sidebar(_open(browsers, "admin", SHELL_PAGE))
    paths = [urlsplit(link).path for link in sidebar.links]

    assert "Developer" in sidebar.headings
    assert ["/apidocs/", "/developer/tokens", "/developer/tokens/new"] == [
        p for p in paths if p.startswith(("/apidocs", "/developer"))
    ]
    assert "/admin/users" in paths
    # The entries the features still draw only in the slot stay, after the
    # registry's, and auth's Users, which the slot draws too, shows once.
    assert sidebar.headings.count("Administration") == 1
    assert paths.index("/admin/users") < paths.index("/admin/settings")
    assert paths.count("/admin/users") == 1


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("who", BROWSERS)
def test_every_asset_a_page_links_on_this_site_is_there(browsers, who, page):
    html = _open(browsers, who, page)

    assets = [
        a for a in _assets_on_this_site(html) if a.split("?")[0] not in UNBUILT_BUNDLES
    ]
    missing = [a for a in assets if browsers[who].get(a).status_code != 200]

    assert assets
    assert missing == []


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("who", BROWSERS)
def test_a_page_asks_no_other_site(browsers, who, page):
    html = _open(browsers, who, page)

    assert [name for name in THIRD_PARTY if name in html] == []


@pytest.mark.parametrize(
    "page", [p for p in PAGES if p not in PAGES_OF_METRONIC_FEATURES]
)
@pytest.mark.parametrize("who", BROWSERS)
def test_a_page_draws_nothing_of_metronic(
    browsers, without_metronic_features, who, page
):
    html = _open(browsers, who, page)

    assert KEENTHEMES.findall(html) == []
    assert KT_ID.findall(html) == []


@pytest.mark.parametrize("who", BROWSERS)
def test_the_header_offers_the_three_modes(browsers, who):
    """uvlhub.io's Mode menu: Light, Dark and System, and the mode is set
    before the stylesheets, so a dark page does not flash light first."""
    html = _open(browsers, who, SHELL_PAGE)
    menu = html[html.index('class="dropdown-menu dropdown-menu-end uvl-mode-menu"') :]
    menu = menu[: menu.index("</div>")]

    assert re.findall(r'data-uvl-theme="(\w+)"', menu) == ["light", "dark", "system"]
    assert html.index("data-bs-theme") < html.index("css/app.css")


@pytest.fixture
def uvlhub_appearance(app):
    """The words the product's seeder writes in theme's Appearance panel,
    taken out again afterwards."""
    from splent_framework.services.service_locator import service_proxy

    from uvlhub_splent.seeders import APPEARANCE, UvlhubAppearanceSeeder

    with app.app_context():
        UvlhubAppearanceSeeder().run()
    yield
    with app.app_context():
        service_proxy("SettingsService").set_many({key: "" for key in APPEARANCE})


@pytest.mark.parametrize("who", BROWSERS)
def test_an_address_that_leads_nowhere_answers_uvlhubs_card(
    browsers, uvlhub_appearance, who
):
    """theme's page, which the product neither shadows nor answers for:
    saying what uvlhub's seeder puts in the Appearance panel, dressed as
    uvlhub.io's card by the product's stylesheet, and asking no other site
    for anything (theme's own tokens would load Inter from Google)."""
    response = browsers[who].get("/this-page-does-not-exist")
    html = response.get_data(as_text=True)

    assert response.status_code == 404
    assert 'class="cms-public"' in html and 'class="error-page"' in html
    assert '<h1 class="error-page__title">Oops!</h1>' in html
    assert "We can&#39;t find that page." in html
    assert ">Return home</a>" in html
    assert "/static/css/uvlhub-error.css" in html
    assert [name for name in THIRD_PARTY if name in html] == []
    assert not (TEMPLATES / "404.html").exists()
    assert not (PACKAGE / "errors.py").exists()


@pytest.mark.parametrize("page", ["400.html", "401.html", "500.html"])
def test_the_errors_no_feature_answers_wear_the_same_card(app, page):
    """The framework renders the product's own page for these, in the
    markup of theme's 404, so one stylesheet draws them all."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(page)

    assert 'class="error-page"' in html
    assert '<a class="btn btn-primary" href="/">' in html
    assert "/static/css/uvlhub-error.css" in html
    assert "css/app.css" not in html


def test_the_dark_mode_is_a_set_of_tokens():
    """The dark mode is the skin's own tokens redefined, so another hub
    reskins both modes where it reskins the light one."""
    skin = (STATIC / "css" / "uvlhub.css").read_text(encoding="utf-8")
    dark = skin[skin.index(':root[data-bs-theme="dark"] {') :]
    dark = dark[: dark.index("}")]

    declared = re.findall(r"^\s*(--[\w-]+):", dark, flags=re.M)
    assert declared and all(name.startswith("--uvl-") for name in declared)


def test_the_logo_is_as_high_as_the_appearance_panel_says(app, browsers):
    from splent_framework.services.service_locator import service_proxy

    with app.app_context():
        service_proxy("SettingsService").set("site_logo_size", "56")
    try:
        html = _open(browsers, "anonymous", SHELL_PAGE)
    finally:
        with app.app_context():
            service_proxy("SettingsService").set("site_logo_size", "")

    brand = html[html.index('class="sidebar-brand uvl-sidebar-logo"') :]
    assert 'height="56"' in brand[: brand.index("</a>")]


def test_the_chrome_icons_are_in_the_sprite(browsers):
    html = _open(browsers, "user", SHELL_PAGE)
    used = set(re.findall(r'<use href="([^"#]+)[^"#]*#(ph-[a-z0-9-]+)"', html))
    sprites = {address for address, _ in used}

    assert used
    for address in sprites:
        response = browsers["user"].get(address)
        assert response.status_code == 200, f"{address} answered {response.status_code}"
        symbols = set(
            re.findall(r'<symbol id="(ph-[a-z0-9-]+)"', response.get_data(as_text=True))
        )
        assert {name for where, name in used if where == address} <= symbols


def test_the_fonts_are_served_by_the_product(browsers):
    stylesheet = (
        browsers["anonymous"].get("/static/css/uvlhub.css").get_data(as_text=True)
    )
    fonts = re.findall(r'url\("\.\./fonts/([^"]+\.woff2)"\)', stylesheet)

    assert len(fonts) == 4
    for font in fonts:
        assert browsers["anonymous"].get(f"/static/fonts/{font}").status_code == 200
    assert (STATIC / "fonts" / "LICENSE.txt").is_file()
    assert (STATIC / "vendor" / "phosphor" / "LICENSE.txt").is_file()


def test_the_product_templates_carry_nothing_of_metronic():
    found = {
        str(path.relative_to(TEMPLATES)): KEENTHEMES.findall(text) + KT_ID.findall(text)
        for path in TEMPLATES.rglob("*.html")
        if (text := path.read_text(encoding="utf-8"))
    }

    assert {path: names for path, names in found.items() if names} == {}


def test_the_product_code_carries_nothing_of_metronic():
    """What splent check:vendor reads in the product's tree, its code
    and comments included."""
    found = {
        str(path.relative_to(PACKAGE)): KEENTHEMES.findall(
            path.read_text(encoding="utf-8")
        )
        for path in PACKAGE.rglob("*.py")
    }

    assert {path: names for path, names in found.items() if names} == {}


def test_the_static_folder_carries_nothing_of_metronic():
    found = {
        str(path.relative_to(STATIC)): KEENTHEMES.findall(
            path.read_text(encoding="utf-8", errors="replace")
        )
        for path in STATIC.rglob("*")
        if path.is_file()
        and path.suffix in TEXT_FILES
        and "uploads" not in path.relative_to(STATIC).parts
    }

    assert {path: names for path, names in found.items() if names} == {}
