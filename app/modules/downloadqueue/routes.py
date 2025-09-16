import os
import zipfile
from io import BytesIO

from flask import render_template, request, send_file

from app.modules.downloadqueue import downloadqueue_bp
from app.modules.hubfile.services import HubfileService

hubfile_service = HubfileService()


@downloadqueue_bp.route("/downloadqueue", methods=["GET"])
def downloadqueue():
    param_files = request.args.get("files", "")
    hubfiles_ids = [int(x) for x in param_files.split(",") if x]
    hubfiles = hubfile_service.get_by_ids(hubfiles_ids)
    return render_template("downloadqueue/queue.html", hubfiles=hubfiles)


@downloadqueue_bp.route("/dataset/build/download/", methods=["GET"])
def download_build_dataset():
    param_files = request.args.get("files", "")
    hubfiles_ids = [int(x) for x in param_files.split(",") if x]
    hubfiles = hubfile_service.get_by_ids(hubfiles_ids)

    # Create Zip
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for hubfile in hubfiles:
            file_path = hubfile.get_full_path()
            if os.path.exists(file_path):
                zf.write(file_path, os.path.basename(file_path))
            else:
                print(f"The file {file_path} does not exist.")

    memory_file.seek(0)

    # Send Zip to user
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name="my_dataset.zip",
    )
