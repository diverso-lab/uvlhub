from app.modules.webhook.models import Webhook
from core.repositories.BaseRepository import BaseRepository


class WebhookRepository(BaseRepository):
    def __init__(self):
        super().__init__(Webhook)
