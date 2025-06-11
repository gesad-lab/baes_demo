import importlib.util
import glob
from pathlib import Path
import os
from typing import List, Tuple

# Streamlit import is optional when running in tests
try:
    import streamlit as st  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    st = None  # Allows importing this module in headless tests without Streamlit


MODULE_CACHE: List[Tuple[str, object]] = []

def discover_ui_modules() -> List[Tuple[str, object]]:
    """Return list of tuples (entity_name, module) for each generated UI module."""
    global MODULE_CACHE
    if MODULE_CACHE:
        return MODULE_CACHE

    ui_path = Path(__file__).resolve().parent.parent / "generated" / "ui"
    for file_path in glob.glob(str(ui_path / "*_ui.py")):
        module_name = Path(file_path).stem  # e.g. student_ui
        entity_name = module_name.replace("_ui", "").capitalize()
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            MODULE_CACHE.append((entity_name, module))
    return MODULE_CACHE


def main():  # pragma: no cover
    modules = discover_ui_modules()
    if st is None:
        print("Streamlit not installed; cannot run UI.")
        return

    if not modules:
        st.write("No UI modules generated yet. Please run the generation pipeline first.")
        return

    st.sidebar.title("BAE Entities")
    entity_names = [name for name, _ in modules]
    selected = st.sidebar.selectbox("Select entity", entity_names)
    module = dict(modules)[selected]

    if hasattr(module, "render"):
        module.render()
    else:
        st.write(f"Module for {selected} does not expose a render() function.")


if __name__ == "__main__":  # pragma: no cover
    main() 