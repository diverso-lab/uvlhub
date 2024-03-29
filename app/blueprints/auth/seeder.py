from app.blueprints.auth.models import User
from app.seeders.BaseSeeder import BaseSeeder


class AuthSeeder(BaseSeeder):
    def run(self):

        users = [
            User(email='user1@example.com', password='1234'),
            User(email='user2@example.com', password='1234'),
        ]

        self.seed(users)
