from splent_framework.app_factory import create_splent_app


def create_app(config_name=None):
    # No profile named: the framework follows SPLENT_ENV (dev, prod, test).
    return create_splent_app(__name__, config_name)
