from flask import render_template, request, send_file

from app.features.downloadqueue import downloadqueue_bp
from app.features.downloadqueue.services import DownloadqueueService

downloadqueue_service = DownloadqueueService()


@downloadqueue_bp.route("/downloadqueue", methods=["GET"])
def downloadqueue():
    file_ids = downloadqueue_service.parse_file_ids(request.args.get("files", ""))
    hubfiles = downloadqueue_service.get_hubfiles(file_ids)
    return render_template("downloadqueue/queue.html", hubfiles=hubfiles)


@downloadqueue_bp.route("/dataset/build/download/", methods=["GET"])
def download_build_dataset():
    file_ids = downloadqueue_service.parse_file_ids(request.args.get("files", ""))
    memory_file = downloadqueue_service.build_zip_for_ids(file_ids)
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name="my_dataset.zip",
    )
