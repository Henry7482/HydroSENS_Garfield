# latex_utils.py
import re
import subprocess
import os
import tempfile
import shutil # For copying files like images

def tex_escape(text):
    """
    Escapes LaTeX special characters in a given string.
    :param text: The input string.
    :return: The string with LaTeX special characters escaped.
    """
    if not isinstance(text, str):
        text = str(text) # Ensure text is a string

    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
        '\n': r'\\newline{}', # Basic newline handling, might need adjustment
    }
    # Regex to find all special characters
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
    return regex.sub(lambda match: conv[match.group()], text)

def compile_latex_to_pdf(latex_content, jobname="report", output_dir="output",
                         use_latexmk=True, latex_engine="xelatex",
                         assets_paths=None, keep_tex_file=False):
    """
    Compiles a LaTeX string into a PDF.

    :param latex_content: String containing the full LaTeX document.
    :param jobname: The base name for output files (e.g., 'report' -> 'report.pdf').
    :param output_dir: Directory where the final PDF (and .tex if kept) will be saved.
    :param use_latexmk: Boolean, True to use latexmk, False to use the specified latex_engine directly.
    :param latex_engine: String, the LaTeX engine to use if not using latexmk (e.g., 'pdflatex', 'xelatex', 'lualatex').
    :param assets_paths: List of paths to asset files (e.g., images) that need to be in the compilation directory.
    :param keep_tex_file: Boolean, True to keep the generated .tex file in the output_dir.
    :return: Path to the generated PDF if successful, None otherwise.
    """
    os.makedirs(output_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_compile_dir:
        tex_filename = f"{jobname}.tex"
        tex_filepath_temp = os.path.join(temp_compile_dir, tex_filename)
        pdf_filepath_temp = os.path.join(temp_compile_dir, f"{jobname}.pdf")
        log_filepath_temp = os.path.join(temp_compile_dir, f"{jobname}.log")
        # Copy assets to temp_compile_dir
        assets_src = os.path.join(os.path.dirname(__file__), '../data/assets')
        assets_dst = os.path.join(temp_compile_dir, 'assets')
        shutil.copytree(assets_src, assets_dst)

        # Write the LaTeX content to a .tex file in the temporary directory
        with open(tex_filepath_temp, "w", encoding="utf-8") as f:
            f.write(latex_content)

        print("Current working directory:", os.getcwd())

        # Copy assets to the temporary compilation directory
        if assets_paths:
            for asset_path in assets_paths:
                if os.path.exists(asset_path):
                    shutil.copy(asset_path, os.path.join(temp_compile_dir, os.path.basename(asset_path)))
                else:
                    print(f"Warning: Asset file not found: {asset_path}")

        if use_latexmk:
            command = [
                "latexmk",
                f"-{latex_engine}", # Specify engine for latexmk
                "-interaction=nonstopmode",
                "-file-line-error", # More precise error messages
                f"-jobname={jobname}",
                tex_filename        # The .tex file to compile
            ]
        else:
            command = [
                latex_engine,
                "-interaction=nonstopmode",
                "-file-line-error",
                f"-jobname={jobname}",
                tex_filename
            ]

        print(f"Running command: {' '.join(command)} in {temp_compile_dir}")

        # Compilation process
        # latexmk often needs to be run once.
        # If not using latexmk, you might need to run the latex_engine multiple times
        # for things like Table of Contents, citations, etc. latexmk handles this.
        num_runs = 1 if use_latexmk else 2 # Basic: 2 runs for xelatex for TOC/refs

        for i in range(num_runs):
            process = subprocess.run(command, cwd=temp_compile_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if process.returncode != 0:
                print(f"--- LaTeX Compilation Failed (Pass {i+1}) ---")
                print(f"Return Code: {process.returncode}")
                print("--- STDOUT ---")
                print(process.stdout)
                print("--- STDERR ---")
                print(process.stderr)
                if os.path.exists(log_filepath_temp):
                    with open(log_filepath_temp, "r", encoding="utf-8") as log_file:
                        print("--- LOG FILE ---")
                        print(log_file.read(2000)) # Print first 2000 chars of log
                return None
            print(f"--- LaTeX Compilation Succeeded (Pass {i+1}) ---")
            if use_latexmk: # latexmk handles multiple runs itself
                break


        final_pdf_path = os.path.join(output_dir, f"{jobname}.pdf")
        final_tex_path = os.path.join(output_dir, f"{jobname}.tex")

        if os.path.exists(pdf_filepath_temp):
            shutil.move(pdf_filepath_temp, final_pdf_path)
            if keep_tex_file:
                shutil.copy(tex_filepath_temp, final_tex_path) # Copy original from temp
            print(f"PDF generated successfully: {final_pdf_path}")
            return final_pdf_path
        else:
            print("--- PDF file not found after compilation attempts. ---")
            if os.path.exists(log_filepath_temp):
                with open(log_filepath_temp, "r", encoding="utf-8") as log_file:
                    print("--- LOG FILE (Final Check) ---")
                    print(log_file.read(2000))
            return None