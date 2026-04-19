import os

from flask import Blueprint, abort, send_from_directory


class BaseBlueprint(Blueprint):
    ALLOWED_ASSET_SUBFOLDERS = ("js", "css", "dist")

    def __init__(
        self,
        name,
        import_name,
        static_folder=None,
        static_url_path=None,
        template_folder=None,
        url_prefix=None,
        subdomain=None,
        url_defaults=None,
        root_path=None,
    ):
        super().__init__(
            name,
            import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix,
            subdomain=subdomain,
            url_defaults=url_defaults,
            root_path=root_path,
        )
        self.module_path = os.path.join(os.getenv("WORKING_DIR", ""), "app", "modules", name)
        self.add_asset_routes()

    def add_asset_routes(self):
        """Define a dynamic route to serve any file inside subfolders under assets (e.g., js, css)."""
        assets_folder = os.path.join(self.module_path, "assets")
        if os.path.exists(assets_folder):
            self.add_url_rule(
                f"/{self.name}/<path:subfolder>/<path:filename>",
                "assets",
                self.send_file,
            )
        else:
            print(f"(BaseBlueprint) -> {assets_folder} does not exist.")

    def send_file(self, subfolder, filename):
        """Serve a file from the module's assets/<subfolder>/ tree.

        Uses send_from_directory so binary assets (wheels, wasm, zip) stream
        correctly with the right MIME type instead of being read as text.
        """
        if filename.endswith("webpack.config.js") or os.path.basename(filename) == "webpack.config.js":
            abort(403, description="Access to this file is forbidden")

        top = subfolder.split("/", 1)[0]
        if top not in self.ALLOWED_ASSET_SUBFOLDERS:
            abort(404, description=f"Invalid path or file: {subfolder}/{filename}")

        assets_root = os.path.join(self.module_path, "assets", subfolder)
        if not os.path.isdir(assets_root):
            abort(404, description=f"Invalid path or file: {subfolder}/{filename}")

        return send_from_directory(assets_root, filename)
