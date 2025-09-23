"""Configuration."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


class Config:
    """Configuration module and helpers."""

    _mod_path: str | None = None

    @classmethod
    def set_config_mod(cls, filename: str | None):
        r"""Set configuration module.

        Parameters
        ----------
        filename
            Name of configuration file to use. This file MUST be located
            in then `pyroids.config` directory. See
            pyroids\config\template.py for instructions to set up a
            configuration file.
        """
        cls._mod_path = (
            None if filename is None else ".config." + filename.replace(".py", "")
        )

    @classmethod
    def get_mod(cls) -> ModuleType | None:
        """Get configuration module or None if no configuration defined."""
        if cls._mod_path is None:
            return None
        return importlib.import_module(cls._mod_path, "pyroids")

    @classmethod
    def import_config(cls, mod_vars: dict, settings: list[str]):
        """Override default settings with configuration file settings.

        Overrides a module's default settings with settings defined in any
        configuration file. Makes no change to any setting not defined in
        the configuration file.

        Parameters
        ----------
        mod_vars
            Module's variables dictionary as returned by vars() when called
            from the module.

        settings
            List of attribute names that each define a default setting on the
            module with variables dictionary passed as `mod_vars`.
        """
        mod = cls.get_mod()
        if mod is None:
            return

        for setting in settings:
            if hasattr(mod, setting):
                mod_vars[setting] = getattr(mod, setting)
