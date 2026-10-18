"""SQLAlchemy models, one module per owner (see PLAN.md).

Importing this package imports every model module in alphabetical order, so all
tables and foreign keys are registered no matter which service starts first.
"""
import importlib
import pkgutil

for _module in sorted(m.name for m in pkgutil.iter_modules(__path__)):
    importlib.import_module(f"{__name__}.{_module}")
