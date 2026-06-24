from app.features.webhook.models import Webhook
from splent_framework.repositories.BaseRepository import BaseRepository


class WebhookRepository(BaseRepository):
    def __init__(self):
        super().__init__(Webhook)
