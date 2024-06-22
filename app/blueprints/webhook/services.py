from app.blueprints.webhook.repositories import WebhookRepository
from core.services.BaseService import BaseService


class Webhook(BaseService):
    def __init__(self):
        super().__init__(WebhookRepository())
