from pathlib import Path

import jinja2


def load_templates(directory: Path) -> dict[str, jinja2.Template]:
    """Load and compile all Jinja text templates in a directory."""
    template_file_suffix = ".txt.j2"
    template_environment = jinja2.Environment(autoescape=False, undefined=jinja2.StrictUndefined)
    return {path.name.removesuffix(template_file_suffix): template_environment.from_string(path.read_text().strip()) for path in directory.glob(f"*{template_file_suffix}")}
