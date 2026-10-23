"""uvlhub's own content for the features it shares with the product line.

The team feature seeds the diversolab directory. uvlhub's team page groups
its people by the organisations behind the project instead, so this
product takes over team's seeder (``replaces``) and seeds one team Role
per organisation, with its description, logo and website, and the people
who belong to it.

theme's page for an address that leads nowhere says what its Appearance
panel says, so the product seeds uvlhub.io's words there.

Images go through the media library with a ``seed://uvlhub/`` source key,
so seeding again reuses the stored file instead of copying it twice.
"""

import os

from splent_framework.seeders.BaseSeeder import BaseSeeder
from splent_framework.services.service_locator import service_proxy
from splent_framework.utils.text import slugify

from splent_io.splent_feature_media.services import MediaService
from splent_io.splent_feature_team.models import Role, TeamMember

STATIC_MEDIA = os.path.join(os.path.dirname(__file__), "static", "media")

# In page order. Each one is a team Role, the section its people appear in.
ORGANISATIONS = [
    {
        "name": "University of Seville, Spain",
        "link": "http://www.us.es",
        "logo": "logos/university_of_seville.svg",
        "description": (
            "Performs active development of the application and is responsible "
            "for code maintenance, deployment, operation of services and new "
            "functionalities."
        ),
    },
    {
        "name": "University of Malaga, Spain",
        "link": "http://www.uma.es",
        "logo": "logos/university_of_malaga.svg",
        "description": "Responsible for active research, technical support",
    },
    {
        "name": "University of Ulm, Germany",
        "link": "http://www.uni-ulm.de",
        "logo": "logos/university_of_ulm.svg",
        "description": (
            "Provides population of consistent datasets with rich metadata for "
            "initial loading of models into UVL. Responsible for the UVL parser. "
            "Active research."
        ),
    },
]

# What uvlhub.io's 404 says, in the fields of theme's Appearance panel.
APPEARANCE = {
    "site_404_title": "Oops!",
    "site_404_text": "We can't find that page.",
    "site_404_cta": "Return home",
}

# ``organisation`` names the Role the member is listed under, whose card
# already names it, so the member has no affiliation of its own: team would
# write it again after the position.
MEMBERS = [
    {
        "name": "David Romero-Organvidez",
        "position": "PhD Student / Project leader",
        "email": "drorganvidez@us.es",
        "organisation": "University of Seville, Spain",
        "photo": "team/david_romero_organvidez.jpg",
    },
]


def _import(relative_path, title):
    return MediaService().import_from_file(
        os.path.join(STATIC_MEDIA, relative_path),
        title=title,
        source_key="seed://uvlhub/" + relative_path,
    )


class UvlhubTeamSeeder(BaseSeeder):
    replaces = ("splent_io.splent_feature_team.seeders",)

    def run(self):
        roles = self.seed(
            [
                Role(
                    name=org["name"],
                    slug=slugify(org["name"]),
                    order=order,
                    description=org["description"],
                    logo=_import(org["logo"], org["name"]).url,
                    link=org["link"],
                )
                for order, org in enumerate(ORGANISATIONS, start=1)
            ]
        )
        by_name = {role.name: role for role in roles}

        members = []
        for order, m in enumerate(MEMBERS, start=1):
            member = TeamMember(
                name=m["name"],
                slug=slugify(m["name"]),
                position=m["position"],
                photo=_import(m["photo"], m["name"]).url,
                email=m["email"],
                order=order,
                published=True,
            )
            member.roles = [by_name[m["organisation"]]]
            members.append(member)
        self.seed(members)


class UvlhubAppearanceSeeder(BaseSeeder):
    """uvlhub.io's words on theme's 404, in the Appearance panel's fields.

    A field an administrator already filled in keeps what they wrote.
    """

    def run(self):
        settings = service_proxy("SettingsService")
        settings.set_many(
            {key: value for key, value in APPEARANCE.items() if not settings.get(key)}
        )
