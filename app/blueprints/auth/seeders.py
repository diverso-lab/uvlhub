from app.blueprints.auth.models import User
from app.blueprints.profile.models import UserProfile
from app.seeders.BaseSeeder import BaseSeeder


class AuthSeeder(BaseSeeder):
    def run(self):

        # Seeding users
        users = [
            User(email='user1@example.com', password='1234'),
            User(email='user2@example.com', password='1234'),
        ]

        # Inserted users with their assigned IDs are returned by `self.seed`.
        seeded_users = self.seed(users)

        # Create profiles for each user inserted.
        user_profiles = []
        for user in seeded_users:
            profile_data = {
                "user_id": user.id,
                "orcid": "",
                "affiliation": "Some University",
                "name": "John",
                "surname": "Doe",
            }
            user_profile = UserProfile(**profile_data)
            user_profiles.append(user_profile)

        # Seeding user profiles
        self.seed(user_profiles)
