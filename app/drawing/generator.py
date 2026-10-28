from pathlib import Path
import copy
import tempfile
import xml.etree.ElementTree as ET
import math

from cadquery import exporters
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def generate_drawing_pdf(
    shape,
    output_pdf_path,
    shape_information=None,
    face_information=None,
    edge_information=None,
    features=None,
):
    """
    Generate a PDF engineering drawing containing top, front, and side views.

    Compatible with CadQuery 2.8.0.
    """

    output_pdf_path = Path(output_pdf_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # Drawing sheet dimensions
    # Drawing sheet dimensions
    sheet_width = 1300
    sheet_height = 800

    
    # First-angle projection layout
    views, drawing_scale = calculate_view_layout(
    shape,
    sheet_width=sheet_width,
    sheet_height=sheet_height,
    )

    # Create the main SVG drawing sheet
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "width": str(sheet_width),
            "height": str(sheet_height),
            "viewBox": f"0 0 {sheet_width} {sheet_height}",
            "version": "1.1",
        },
    )

    # Drawing border
    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {
            "x": "15",
            "y": "15",
            "width": str(sheet_width - 30),
            "height": str(sheet_height - 30),
            "fill": "none",
            "stroke": "black",
            "stroke-width": "1",
        },
    )

    # Drawing title
    #It creates a new XML element and attaches it to an existing parent element.
    title = ET.SubElement(
        root,
        f"{{{SVG_NS}}}text",
        {
            "x": "35",
            "y": "45",
            "font-family": "Arial",
            "font-size": "22",
            "font-weight": "bold",
            "fill": "black",
        },
    )
    title.text = "CADraft - Engineering Drawing"

    # -------------------------------------------------
    # DRAWING TITLE BLOCK
    # -------------------------------------------------

    title_block_x = 800
    title_block_y = 710
    title_block_width = 470
    title_block_height = 70

    # Outer border
    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {
            "x": str(title_block_x),
            "y": str(title_block_y),
            "width": str(title_block_width),
            "height": str(title_block_height),
            "fill": "white",
            "stroke": "black",
            "stroke-width": "1",
        },
    )

    # Horizontal divider
    add_svg_line(
        root,
        title_block_x,
        title_block_y + 35,
        title_block_x + title_block_width,
        title_block_y + 35,
    )

    # Vertical divider
    add_svg_line(
        root,
        title_block_x + 300,
        title_block_y,
        title_block_x + 300,
        title_block_y + title_block_height,
    )

    # Title block labels
    add_svg_text(
        root,
        title_block_x + 10,
        title_block_y + 15,
        "DRAWING: CADraft Engineering Drawing",
        size=11,
        bold=True,
    )

    add_svg_text(
        root,
        title_block_x + 10,
        title_block_y + 52,
        "UNITS: mm",
        size=10,
    )

    add_svg_text(
        root,
        title_block_x + 310,
        title_block_y + 15,
        "SCALE: NTS",
        size=10,
    )

    add_svg_text(
        root,
        title_block_x + 310,
        title_block_y + 32,
        "PROJECTION: FIRST ANGLE",
        size=10,
    )

    add_svg_text(
        root,
        title_block_x + 310,
        title_block_y + 52,
        "REVISION: 00",
        size=10,
    )


    # -------------------------------------------------
    # PART SPECIFICATIONS
    # -------------------------------------------------

    shape_information = shape_information or {}
    face_information = face_information or []
    edge_information = edge_information or []
    features = features or []

    panel_x = 980
    panel_y = 100
    panel_width = 290

    specifications = [
        ("Length X", shape_information.get("length", "N/A")),
        ("Width Y", shape_information.get("width", "N/A")),
        ("Height Z", shape_information.get("height", "N/A")),
        ("Solids", shape_information.get("solids", "N/A")),
        ("Faces", shape_information.get("faces", "N/A")),
        ("Edges", shape_information.get("edges", "N/A")),
    ]

    row_height = 28
    panel_height = 48 + len(specifications) * row_height

    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {
            "x": str(panel_x),
            "y": str(panel_y),
            "width": str(panel_width),
            "height": str(panel_height),
            "fill": "white",
            "stroke": "black",
            "stroke-width": "1",
        },
    )

    add_svg_text(
        root,
        panel_x + 10,
        panel_y + 25,
        "PART SPECIFICATIONS",
        size=15,
        bold=True,
    )

    for index, (label, value) in enumerate(specifications):
        y = panel_y + 50 + index * row_height

        if isinstance(value, (int, float)):
            value = f"{value:.2f}" if isinstance(value, float) else str(value)

        add_svg_text(root, panel_x + 10, y, label, size=12)
        add_svg_text(root, panel_x + 155, y, value, size=12)

    # Detected cylindrical feature summary
    feature_y = panel_y + panel_height + 35

    add_svg_text(
        root,
        panel_x,
        feature_y,
        "CYLINDRICAL FEATURES",
        size=14,
        bold=True,
    )

    if not features:
        add_svg_text(
            root,
            panel_x,
            feature_y + 25,
            "No cylindrical features detected",
            size=11,
        )
    else:
        for index, feature in enumerate(features[:8], start=1):
            params = feature.parameters
            diameter = params.get("diameter", 0)
            location = params.get("location", {})

            description = (
                f"{index}. Dia {diameter:.2f} | "
                f"X {location.get('x', 0):.2f}, "
                f"Y {location.get('y', 0):.2f}, "
                f"Z {location.get('z', 0):.2f}"
            )

            add_svg_text(
                root,
                panel_x,
                feature_y + 22 + index * 22,
                description,
                size=10,
            )


    # IMPORTANT:
    # All SVG and PDF processing must happen before TemporaryDirectory closes.
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        for index, view in enumerate(views, start=1):
            svg_path = temp_dir / f"view_{index}.svg"

            # CadQuery 2.8.0: use exporters.export() and opt=.
            exporters.export(
                shape,
                str(svg_path),
                exporters.ExportTypes.SVG,
                opt={
                    "width": view["width"],
                    "height": view["height"],
                    "marginLeft": 15,
                    "marginTop": 25,
                    "projectionDir": view["direction"],
                    "up": view["up"],
                    "showAxes": False,
                    "showHidden": True,
                    "strokeWidth": 0.8,
                    "strokeColor": (0, 0, 0),
                    "hiddenColor": (160, 160, 160),
                },
            )

            # Read the generated SVG
            view_tree = ET.parse(svg_path)
            view_root = view_tree.getroot()

            # Preserve the SVG geometry group, including its transforms
            geometry_group = view_root.find(f"{{{SVG_NS}}}g")

            if geometry_group is None:
                raise RuntimeError(
                    f"Could not find projected geometry in {svg_path}"
                )

            # Place the view on the drawing sheet
            placement = ET.SubElement(
                root,
                f"{{{SVG_NS}}}g",
                {
                    "transform": (
                        f"translate({view['x']},{view['y']})"
                    )
                },
            )

            #What does deepcopy() do?
            #    It creates an independent copy of the XML element and its descendants.

            #    This allows the function to reuse the exported geometry without moving or modifying the element in the original parsed SVG tree.
            placement.append(copy.deepcopy(geometry_group))

            # Add view label
            label = ET.SubElement(
                placement,
                f"{{{SVG_NS}}}text",
                {
                    "x": "10",
                    "y": "15",
                    "font-family": "Arial",
                    "font-size": "14",
                    "font-weight": "bold",
                    "fill": "black",
                    "stroke": "none",
                },
            )
            label.text = view["name"]

        # Save the combined SVG inside the temporary directory
        combined_svg_path = temp_dir / "combined_drawing.svg"

        ET.ElementTree(root).write(
            combined_svg_path,
            encoding="utf-8",
            xml_declaration=True,
        )

        # Convert combined SVG to a ReportLab drawing svg2rlg() reads the combined SVG and attempts to convert it into a ReportLab drawing object.
        drawing = svg2rlg(str(combined_svg_path))

        if drawing is None:
            raise RuntimeError(
                "Could not convert the combined SVG to PDF."
            )

        # Generate the final PDF at the requested output location
        renderPDF.drawToFile(
            drawing,
            str(output_pdf_path),
        )

    print(f"PDF drawing generated: {output_pdf_path}")

    return output_pdf_path



def calculate_view_layout(shape, sheet_width=1300, sheet_height=800):
    """
    Calculate view canvas sizes and positions from the STEP model's
    bounding box.

    Assumes the model's X, Y and Z axes correspond to its principal
    drawing directions. This is an initial layout engine, not a
    complete arbitrary-orientation projection solution.
    """

    bbox = shape.val().BoundingBox()

    length = bbox.xlen
    width = bbox.ylen
    height = bbox.zlen

    # Available drawing area, leaving room for the specifications panel.
    area_left = 30
    area_top = 90
    area_width = 900
    area_height = 570

    # Dimensions of the projected views in model units.
    projected = {
        "RIGHT-SIDE VIEW": (width, height),
        "FRONT VIEW": (length, height),
        "TOP VIEW": (length, width),
        "ISOMETRIC VIEW": (
            (length + width) * 0.7071,
            height * 0.8165 + (length + width) * 0.4082,
        ),
    }

    # Reserve gaps between the view canvases.
    gap = 25

    # Estimate the combined arrangement's dimensions.
    # Side + front + isometric are arranged horizontally.
    row_width = (
        projected["RIGHT-SIDE VIEW"][0]
        + projected["FRONT VIEW"][0]
        + projected["ISOMETRIC VIEW"][0]
        + 2 * gap
    )

    row_height = max(
        projected[name][1]
        for name in ("RIGHT-SIDE VIEW", "FRONT VIEW", "ISOMETRIC VIEW")
    )

    # The top view is below the front view.
    total_height = row_height + gap + projected["TOP VIEW"][1]
    total_width = max(
        row_width,
        projected["TOP VIEW"][0],
    )

    # One common scale for all views.
    scale = min(
        area_width / total_width,
        area_height / total_height,
    )

    # Add padding around each view's projected geometry.
    margin_x = 30
    margin_y = 35

    views = [
        {
            "name": "RIGHT-SIDE VIEW",
            "direction": (1, 0, 0),
            "up": (0, 0, 1),
            "projected_width": projected["RIGHT-SIDE VIEW"][0],
            "projected_height": projected["RIGHT-SIDE VIEW"][1],
        },
        {
            "name": "FRONT VIEW",
            "direction": (0, 1, 0),
            "up": (0, 0, 1),
            "projected_width": projected["FRONT VIEW"][0],
            "projected_height": projected["FRONT VIEW"][1],
        },
        {
            "name": "TOP VIEW",
            "direction": (0, 0, 1),
            "up": (0, 1, 0),
            "projected_width": projected["TOP VIEW"][0],
            "projected_height": projected["TOP VIEW"][1],
        },
        {
            "name": "ISOMETRIC VIEW",
            "direction": (1, -1, 1),
            "up": (0, 0, 1),
            "projected_width": projected["ISOMETRIC VIEW"][0],
            "projected_height": projected["ISOMETRIC VIEW"][1],
        },
    ]

    for view in views:
        view["width"] = max(
            100,
            math.ceil(view["projected_width"] * scale + 2 * margin_x),
        )
        view["height"] = max(
            100,
            math.ceil(view["projected_height"] * scale + 2 * margin_y),
        )

    # Place side, front and isometric views in a row.
    side, front, top, iso = views

    row_y = area_top + margin_y

    side["x"] = area_left
    side["y"] = row_y

    front["x"] = side["x"] + side["width"] + gap
    front["y"] = row_y

    iso["x"] = front["x"] + front["width"] + gap
    iso["y"] = row_y

    # Center the top view under the front view.
    top["x"] = (
        front["x"]
        + (front["width"] - top["width"]) // 2
    )
    top["y"] = (
        row_y
        + max(side["height"], front["height"], iso["height"])
        + gap
    )

    # Store the calculated common scale for diagnostics.
    print(f"Model bounding box: {length:.2f} x {width:.2f} x {height:.2f} mm")
    print(f"Calculated layout scale: {scale:.3f} drawing units/mm")

    return views, scale


def add_svg_text(root, x, y, text, size=13, bold=False):
    element = ET.SubElement(
        root,
        f"{{{SVG_NS}}}text",
        {
            "x": str(x),
            "y": str(y),
            "font-family": "Arial",
            "font-size": str(size),
            "font-weight": "bold" if bold else "normal",
            "fill": "black",
        },
    )
    element.text = str(text)
    return element


def add_svg_line(root, x1, y1, x2, y2, stroke="black", width=1):
    return ET.SubElement(
        root,
        f"{{{SVG_NS}}}line",
        {
            "x1": str(x1),
            "y1": str(y1),
            "x2": str(x2),
            "y2": str(y2),
            "stroke": stroke,
            "stroke-width": str(width),
        },
    )


def add_dimension(root, x1, y1, x2, y2, label, offset=20):
    """
    Draw a simple horizontal or vertical dimension line.

    Coordinates are SVG drawing-sheet coordinates.
    This helper is intended for dimensions whose projected
    endpoints are already known.
    """
    if abs(y2 - y1) < 0.001:
        # Horizontal dimension
        dim_y = y1 + offset

        add_svg_line(root, x1, y1, x1, dim_y + 5)
        add_svg_line(root, x2, y2, x2, dim_y + 5)
        add_svg_line(root, x1, dim_y, x2, dim_y)

        # Arrowheads
        add_svg_line(root, x1, dim_y, x1 + 6, dim_y - 3)
        add_svg_line(root, x1, dim_y, x1 + 6, dim_y + 3)
        add_svg_line(root, x2, dim_y, x2 - 6, dim_y - 3)
        add_svg_line(root, x2, dim_y, x2 - 6, dim_y + 3)

        add_svg_text(
            root,
            (x1 + x2) / 2,
            dim_y - 5,
            label,
            size=12,
        )

    elif abs(x2 - x1) < 0.001:
        # Vertical dimension
        dim_x = x1 + offset

        add_svg_line(root, x1, y1, dim_x + 5, y1)
        add_svg_line(root, x2, y2, dim_x + 5, y2)
        add_svg_line(root, dim_x, y1, dim_x, y2)

        add_svg_line(root, dim_x, y1, dim_x - 3, y1 + 6)
        add_svg_line(root, dim_x, y1, dim_x + 3, y1 + 6)
        add_svg_line(root, dim_x, y2, dim_x - 3, y2 - 6)
        add_svg_line(root, dim_x, y2, dim_x + 3, y2 - 6)

        add_svg_text(
            root,
            dim_x + 5,
            (y1 + y2) / 2,
            label,
            size=12,
        )

