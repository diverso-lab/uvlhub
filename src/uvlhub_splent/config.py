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

    # uvlhub.io's palette and Inter for theme's public shell, which in uvlhub
    # draws the page of an address that leads nowhere (errors/404.html). No
    # font_url: Inter comes from the product (css/uvlhub-public.css), never
    # from Google. theme 0.13 reads its tokens from here only; the release
    # after it also reads THEME_TOKENS from [tool.splent.config], where this
    # can move once that release is pinned.
    THEME_TOKENS = {
        "primary": "#1b84ff",
        "primary_contrast": "#ffffff",
        "accent": "#287fb9",
        "bg": "#ffffff",
        "surface": "#f9f9f9",
        "text": "#071437",
        "heading": "#071437",
        "muted": "#99a1b7",
        "border": "#f1f1f4",
        "radius": ".475rem",
        "font_body": '"Inter", Helvetica, sans-serif',
        "font_heading": '"Inter", Helvetica, sans-serif',
        "font_display": '"Inter", Helvetica, sans-serif',
        "font_url": "",
    }


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
