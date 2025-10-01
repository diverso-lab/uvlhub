from app.modules.flamapy.services import FlamapyService

def check_uvl(filepath: str):
    service = FlamapyService()
    return service.check_uvl(filepath)
