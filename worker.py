import logging
import os
import redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv
from app import create_app, db
import subprocess  # Importar el módulo subprocess

# Cargar las variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

# Ejecutar 'ls' para listar el contenido del directorio /app


# Escuchar la cola "default"
listen = ['default']

redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    
    logger.info("Listing contents of /app directory:")
    subprocess.run(["ls", "-la", "/app"])
    subprocess.run(["echo", "'mostrando...'"])
    subprocess.run(["cat", "/app/.moduleignore"])

    # Crear la aplicación para que tenga el contexto necesario
    app = create_app()

    with app.app_context():
        # Conectar a Redis y empezar a escuchar la cola
        with Connection(conn):
            worker = Worker(list(map(Queue, listen)))
            worker.work()
