"""Auto-discovery of replacement rules from a configurable package.

Set the ``DAC_WEB_RULES_PACKAGE`` environment variable to point to your
own rules package. Default: ``dac_web.rules``.
"""

import importlib
import logging
import os
import pkgutil

from dac_web.import_replace import ReplacementRegistry, ActionReplacementRule

logger = logging.getLogger(__name__)

_DEFAULT_PACKAGE = "dac_web.rules"


def _iter_subclasses(mod, base=ActionReplacementRule):
    for name in dir(mod):
        obj = getattr(mod, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, base)
            and obj is not base
        ):
            yield obj


def discover_rules(package: str | None = None):
    """Import *package* and register every ``ActionReplacementRule`` subclass found.

    Called once at application startup.
    """
    pkg = package or os.environ.get("DAC_WEB_RULES_PACKAGE", _DEFAULT_PACKAGE)

    try:
        rules_pkg = importlib.import_module(pkg)
    except ModuleNotFoundError:
        logger.warning(
            "Rules package %r not found — no replacement rules loaded", pkg
        )
        return

    registry = ReplacementRegistry.instance()

    if hasattr(rules_pkg, "__path__"):
        for _, mod_name, _ in pkgutil.iter_modules(rules_pkg.__path__):
            full_name = f"{pkg}.{mod_name}"
            try:
                mod = importlib.import_module(full_name)
            except Exception:
                logger.exception("Failed to import rules module %r", full_name)
                continue
            for rule_cls in _iter_subclasses(mod):
                registry.register(rule_cls())
                logger.info(
                    "Registered rule %r (source_class=%r) from %r",
                    rule_cls.name, rule_cls.source_class, full_name,
                )
    else:
        for rule_cls in _iter_subclasses(rules_pkg):
            registry.register(rule_cls())
            logger.info(
                "Registered rule %r (source_class=%r) from %r",
                rule_cls.name, rule_cls.source_class, pkg,
            )

    logger.info(
        "Loaded %d replacement rule(s) from %r", registry.rule_count, pkg
    )
