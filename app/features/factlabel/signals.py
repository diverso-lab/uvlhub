from app.features.hubfile.signals import hubfile_created
from app.managers.task_queue_manager import TaskQueueManager

FACTLABEL_TASK = "app.features.factlabel.tasks.compute_factlabel"


@hubfile_created.connect
def enqueue_factlabel_computation(sender, hubfile_id, path, **kwargs):
    """When a hubfile is created, compute its fact label (full + light)."""
    TaskQueueManager().enqueue_task(FACTLABEL_TASK, hubfile_id=hubfile_id, timeout=5)
    TaskQueueManager().enqueue_task(FACTLABEL_TASK, hubfile_id=hubfile_id, light_fact_label=True, timeout=5)
