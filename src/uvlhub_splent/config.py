"""
Configuration for uvlhub_splent.

Each class extends the framework's base configuration. Only override
what your product needs — everything else is inherited automatically.

Hierarchy (later layers win):
  1. Framework defaults (Config base class)
  2. This file (product config)
  3. Feature inject_config() calls
"""

from splent_framework.configuration.default_config import (
    DevelopmentConfig as BaseDev,
    TestingConfig as BaseTest,
    ProductionConfig as BaseProd,
)


class UvlhubConfig:
    """What every environment of uvlhub shares."""

    # The pages the features write for the public site (public's home,
    # team's list and profiles) in uvlhub's app shell, with the sidebar, as
    # uvlhub.io draws them, through the product's public layer over it. A
    # framework setting no feature reads, so it is the product's to set here.
    SPLENT_SHELL_PUBLIC = "uvlhub_public.html"


class DevelopmentConfig(UvlhubConfig, BaseDev):
    # Add product-specific dev settings here.
    # Example: EXPLAIN_TEMPLATE_LOADING = True
    pass


class TestingConfig(UvlhubConfig, BaseTest):
    # Add product-specific test settings here.
    # Example: PRESERVE_CONTEXT_ON_EXCEPTION = False
    pass


class ProductionConfig(UvlhubConfig, BaseProd):
    # Add product-specific production settings here.
    # Example: SESSION_COOKIE_SECURE = True
    pass
