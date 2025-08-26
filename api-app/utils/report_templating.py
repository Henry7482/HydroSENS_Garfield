import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .latex_utils import tex_escape # Import the escape function

def render_latex_template(template_file_path, data, template_dir="templates"):
    """
    Renders a LaTeX template with provided data using Jinja2.

    :param template_file_path: Path to the Jinja2/LaTeX template file (e.g., 'report_template.tex.j2').
    :param data: A dictionary containing data to populate the template.
    :param template_dir: Directory where the template file is located.
    :return: Rendered LaTeX content as a string.
    """
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml']), # Usually False for .tex, or selective
        block_start_string='\\BLOCK{',  # Custom delimiters for Jinja to avoid clash with LaTeX
        block_end_string='}',
        variable_start_string='\\VAR{',
        variable_end_string='}',
        comment_start_string='\\#{',
        comment_end_string='}',
        line_statement_prefix='%%',
        line_comment_prefix='%#',
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Make the tex_escape function available in templates as a filter
    env.filters['e'] = tex_escape
    # Or use env.globals['tex_escape'] = tex_escape if you prefer calling it as a function

    template = env.get_template(os.path.basename(template_file_path))
    rendered_latex = template.render(data)
    
    return rendered_latex

def render_latex_from_string_template(latex_template_string, data):
    """
    Renders a LaTeX template string with provided data using Jinja2.

    :param latex_template_string: The LaTeX template as a raw string.
    :param data: A dictionary containing data to populate the template.
    :return: Rendered LaTeX content as a string.
    """
    env = Environment(
        autoescape=select_autoescape(), # Usually False for .tex
        block_start_string='\\BLOCK{',
        block_end_string='}',
        variable_start_string='\\VAR{',
        variable_end_string='}',
        comment_start_string='\\#{',
        comment_end_string='}',
        line_statement_prefix='%%',
        line_comment_prefix='%#',
        trim_blocks=True,
        lstrip_blocks=True
    )
    env.filters['e'] = tex_escape
    template = env.from_string(latex_template_string)
    rendered_latex = template.render(data)
    return rendered_latex