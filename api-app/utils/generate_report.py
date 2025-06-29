# generate_report.py
import os
from .report_templating import render_latex_template
from .latex_utils import compile_latex_to_pdf
from .generate_content import generate_content
from data.templates.mock_data import report_data
from .satellite_map_generator import generate_region_satellite_map, extract_coordinates_from_metrics
from .generate_graph import generate_graphs

def run_generate_report(metrics_data):
    # --- Configuration ---
    TEMPLATE_DIR = "/app/data/templates"  # Directory where the LaTeX template is stored
    TEMPLATE_FILENAME = "report_template.tex.j2" # Assumes file-based template
    OUTPUT_DIR = "./generated_reports"
    REPORT_JOBNAME = "RSS_Hydro_Region_Report_2025"
    KEEP_TEX = True # Set to False to delete the .tex file after compilation

    # --- 1. Get data for the Report ---
    print("Step 1: Generating content...")
    report_data = generate_content(metrics_data)
    # report_data = metrics_data # FOR DEMO ONLY

    # --- 2. Generate graphs using Mathplotlib ---
    """
    Use metrics_data to generate timeseries graphs, save as image in assets/graphs.
    Add image path to each metric datapoint by id (graph_image_path)
    """  
    print("Step 2: Generating graphs...")
    # This function should be defined in your utils/generate_graph.py
    report_data = generate_graphs(metrics_data, report_data)
    if not report_data:
        print("No graphs generated, check metrics_data format.")
    else:
        print("Graphs generated successfully")


    print("Step 3: Generating region satellite map...")
        
    # Extract coordinates from your metrics data
    coordinates = extract_coordinates_from_metrics(metrics_data)
    print(f"  Using coordinates: {coordinates[:2]}..." if len(coordinates) > 2 else f"  Using coordinates: {coordinates}")
    
    # Generate the satellite map (replaces your existing region screenshot)
    success = generate_region_satellite_map(
        coordinates=coordinates,
        output_path="assets/images/region_screenshot.png",  # Same path as before
        figsize=(12, 8),  # Adjust size as needed
        alpha=0.5,        # Semi-transparent overlay
        edge_color='none',  # Red border
        face_color='none',  # Yellow fill
        line_width=3,
        zoom='auto'       # Auto-detect zoom level
    )
    report_data["region_screenshot_path"] = "assets/images/region_screenshot.png"  # Update report data with new screenshot path

    if success:
        print("Region satellite map generated successfully")
    else:
        print("Satellite map generation failed, but file may still exist")


    # --- 4. Render the LaTeX template ---
    print("Step 4: Rendering LaTeX template...")
    # Option A: Load template from file
    template_full_path = os.path.join(TEMPLATE_DIR, TEMPLATE_FILENAME)
    if not os.path.exists(template_full_path):
        print(f"Error: Template file not found at {template_full_path}")
        print("Please create 'templates/report_template.tex.j2' or check the path.")
        return

    rendered_latex = render_latex_template(template_full_path, report_data, TEMPLATE_DIR)
    
    # Option B: Use a raw string template (if you prefer not to use files for templates)
    # raw_latex_template_string = r""" \documentclass{article} ... \VAR{your_data | e} ... \end{document} """
    # rendered_latex = render_latex_from_string_template(raw_latex_template_string, report_data)

    if not rendered_latex:
        print("Failed to render LaTeX template.")
        return
    print("\n--- Rendered LaTeX ---")
    # print(rendered_latex[:1000] + "...\n--------------------")


    # --- 5. Compile the rendered LaTeX to PDF ---
    print("\nStep 5: Compiling LaTeX to PDF...")
    pdf_file_path = compile_latex_to_pdf(
        latex_content=rendered_latex,
        jobname=REPORT_JOBNAME,
        output_dir=OUTPUT_DIR,
        use_latexmk=True, # Recommended
        latex_engine="xelatex", # latexmk will use this engine
        assets_paths=None,
        keep_tex_file=KEEP_TEX
    )

    if pdf_file_path:
        print(f"\nReport generation successful! PDF saved to: {pdf_file_path}")
    else:
        print("\nReport generation failed.")

    return pdf_file_path

# For demo
if __name__ == "__main__":
    run_generate_report(report_data)