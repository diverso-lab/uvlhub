"""uvlhub's own content for the features it shares with the product line.

The team and partners features seed the diversolab directory; uvlhub shows
the organisations behind the project instead, so this product takes over
their seeders (``replaces``) and seeds what uvlhub's team page lists.
"""

import os

from splent_framework.seeders.BaseSeeder import BaseSeeder
from splent_framework.utils.text import slugify

from splent_io.splent_feature_media.services import MediaService
from splent_io.splent_feature_partners.models import Partner
from splent_io.splent_feature_team.models import TeamMember

STATIC_MEDIA = os.path.join(os.path.dirname(__file__), "static", "media")

# In page order. The names are the keys team_uvlhub uses for descriptions and
# that members' ``affiliation`` must match.
ORGANISATIONS = [
    {
        "name": "University of Seville, Spain",
        "link": "http://www.us.es",
        "logo": "logos/university_of_seville.svg",
    },
    {
        "name": "University of Malaga, Spain",
        "link": "http://www.uma.es",
        "logo": "logos/university_of_malaga.svg",
    },
    {
        "name": "University of Ulm, Germany",
        "link": "http://www.uni-ulm.de",
        "logo": "logos/university_of_ulm.svg",
    },
]

MEMBERS = [
    {
        "name": "David Romero-Organvidez",
        "position": "PhD Student / Project leader",
        "email": "drorganvidez@us.es",
        "affiliation": "University of Seville, Spain",
        "photo": "team/david_romero_organvidez.jpg",
    },
]


def _import(relative_path, title):
    item = MediaService().import_from_file(
        os.path.join(STATIC_MEDIA, relative_path),
        title=title,
        source_key="seed://uvlhub/" + relative_path,
    )
    return item


class UvlhubTeamSeeder(BaseSeeder):
    replaces = (
        "splent_io.splent_feature_team.seeders",
        "splent_io.splent_feature_partners.seeders",
    )

    def run(self):
        self.seed(
            [
                Partner(
                    media_id=_import(org["logo"], org["name"]).id,
                    name=org["name"],
                    link=org["link"],
                    order=order,
                    active=True,
                )
                for order, org in enumerate(ORGANISATIONS, start=1)
            ]
        )
        self.seed(
            [
                TeamMember(
                    name=m["name"],
                    slug=slugify(m["name"]),
                    position=m["position"],
                    affiliation=m["affiliation"],
                    photo=_import(m["photo"], m["name"]).url,
                    email=m["email"],
                    order=order,
                    published=True,
                )
                for order, m in enumerate(MEMBERS, start=1)
            ]
        )
