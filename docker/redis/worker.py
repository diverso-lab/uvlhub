import os
import logging
from dotenv import load_dotenv
from rq import Worker, Queue
from core.managers.config_manager import ConfigManager
from app import create_app, mail_service

# 🔹 Cargar variables de entorno desde .env
load_dotenv()

# 🔹 Configurar logger base
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # 🚀 Crear la aplicación Flask con la configuración base
    config_name = os.getenv("FLASK_ENV", "development")
    app = create_app(config_name=config_name)

    # ⚙️ Cargar la configuración completa usando tu ConfigManager (igual que en create_app)
    config_manager = ConfigManager(app)
    config_manager.load_config(config_name=config_name)

    # ✅ Ejecutar el worker dentro del contexto de la app
    with app.app_context():
        # 📬 Inicializar el servicio de correo (necesario para URL externas, plantillas, etc.)
        mail_service.init_app(app)

        # 🧠 Obtener conexión Redis desde la configuración Flask
        redis_connection = app.config.get("SESSION_REDIS")

        if not redis_connection:
            raise RuntimeError("❌ Redis connection not found in configuration (SESSION_REDIS).")

        # 🔄 Colas a escuchar
        listen = os.getenv("RQ_QUEUES", "default").split(",")

        # 📦 Crear las colas RQ
        queues = [Queue(name.strip(), connection=redis_connection) for name in listen]

        # 🧩 Iniciar el worker
        logger.info(f"🚀 Starting RQ worker for queues: {listen}")
        worker = Worker(queues, connection=redis_connection)
        worker.work()
