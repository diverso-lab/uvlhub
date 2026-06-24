from app.features.hubfile.signals import hubfile_created
from app.managers.task_queue_manager import TaskQueueManager

TRANSFORM_TASK = "app.features.flamapy.tasks.transform_uvl"


@hubfile_created.connect
def enqueue_uvl_transformation(sender, hubfile_id, path, **kwargs):
    """When a hubfile is created, transform its UVL into the export formats."""
    TaskQueueManager().enqueue_task(TRANSFORM_TASK, path=path, timeout=5)
