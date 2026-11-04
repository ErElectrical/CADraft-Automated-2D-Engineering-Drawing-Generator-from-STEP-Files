from pathlib import Path

import copy

import tempfile

import xml.etree.ElementTree as ET

import math

import re

import cadquery as cq
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt



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

    holes=None,

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

    holes = holes or []



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
        root, panel_x, feature_y,
        "CYLINDRICAL FEATURES", size=14, bold=True,
    )

    if not features:
        add_svg_text(
            root, panel_x, feature_y + 25,
            "No cylindrical features detected", size=11,
        )
    else:
        for index, feature in enumerate(features[:8], start=1):
            params = feature.parameters if hasattr(feature, "parameters") else feature.get("parameters", {})
            diameter = params.get("diameter", 0)
            location = params.get("location", {}) or {}
            description = (
                f"{index}. Dia {float(diameter):.2f} | "
                f"X {float(location.get('x', 0)):.2f}, "
                f"Y {float(location.get('y', 0)):.2f}, "
                f"Z {float(location.get('z', 0)):.2f}"
            )
            add_svg_text(
                root, panel_x, feature_y + 22 + index * 22,
                description, size=10,
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



            # Calculate the actual projected geometry bounds after applying

            # CadQuery's SVG scale/translate transform. These are view-local

            # coordinates, so dimension endpoints align with the visible part.

            bounds = get_svg_geometry_bounds(geometry_group)

            if bounds is not None:

                min_x, min_y, max_x, max_y = bounds

                view_name = view["name"]



                if view_name == "FRONT VIEW":

                    add_dimension(

                        placement, min_x, max_y, max_x, max_y,

                        f"{float(shape_information.get('length', view['projected_width'])):.2f} mm"

                        if shape_information else f"{view['projected_width']:.2f} mm",

                        offset=22,

                    )

                    add_dimension(

                        placement, max_x, min_y, max_x, max_y,

                        f"{float(shape_information.get('height', view['projected_height'])):.2f} mm"

                        if shape_information else f"{view['projected_height']:.2f} mm",

                        offset=22,

                    )

                elif view_name == "RIGHT-SIDE VIEW":

                    add_dimension(

                        placement, min_x, max_y, max_x, max_y,

                        f"{float(shape_information.get('width', view['projected_width'])):.2f} mm"

                        if shape_information else f"{view['projected_width']:.2f} mm",

                        offset=22,

                    )

                    add_dimension(

                        placement, max_x, min_y, max_x, max_y,

                        f"{float(shape_information.get('height', view['projected_height'])):.2f} mm"

                        if shape_information else f"{view['projected_height']:.2f} mm",

                        offset=22,

                    )

                elif view_name == "TOP VIEW":

                    add_dimension(

                        placement, min_x, max_y, max_x, max_y,

                        f"{float(shape_information.get('length', view['projected_width'])):.2f} mm"

                        if shape_information else f"{view['projected_width']:.2f} mm",

                        offset=22,

                    )

                    add_dimension(

                        placement, max_x, min_y, max_x, max_y,

                        f"{float(shape_information.get('width', view['projected_height'])):.2f} mm"

                        if shape_information else f"{view['projected_height']:.2f} mm",

                        offset=22,

                    )
            # Add grouped hole callouts to orthographic views only.
            if holes and view["name"] != "ISOMETRIC VIEW" and bounds is not None:
                add_hole_callouts(
                    placement, view, geometry_group, holes, bounds=bounds
                )
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







def get_svg_geometry_bounds(geometry_group):

    """Return projected path bounds in the exported SVG group's local canvas.



    CadQuery exports line geometry in model coordinates and applies a group

    transform such as `scale(sx, sy) translate(tx, ty)`. This helper parses

    the common M/L/H/V path commands and applies that transform so dimensions

    use the rendered part edges instead of the SVG canvas boundaries.

    """

    transform = geometry_group.get("transform", "")

    scale_match = re.search(

        r"scale\(\s*([-+0-9.eE]+)(?:\s*[, ]\s*([-+0-9.eE]+))?\s*\)",

        transform,

    )

    translate_match = re.search(

        r"translate\(\s*([-+0-9.eE]+)(?:\s*[, ]\s*([-+0-9.eE]+))?\s*\)",

        transform,

    )

    sx = float(scale_match.group(1)) if scale_match else 1.0

    sy = float(scale_match.group(2) or scale_match.group(1)) if scale_match else 1.0

    tx = float(translate_match.group(1)) if translate_match else 0.0

    ty = float(translate_match.group(2) or 0.0) if translate_match else 0.0



    points = []

    number = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"

    token_pattern = re.compile(rf"([MLHVmlhv])|({number})")



    for path in geometry_group.iter(f"{{{SVG_NS}}}path"):

        data = path.get("d", "")

        tokens = [command if command else value

                  for command, value in token_pattern.findall(data)]

        i = 0

        command = None

        current_x = current_y = 0.0

        while i < len(tokens):

            token = tokens[i]

            if token in "MLHVmlhv":

                command = token

                i += 1

                continue

            if command is None:

                i += 1

                continue

            try:

                if command in ("M", "L", "m", "l") and i + 1 < len(tokens):

                    x, y = float(tokens[i]), float(tokens[i + 1])

                    i += 2

                    if command in ("m", "l"):

                        x += current_x

                        y += current_y

                    current_x, current_y = x, y

                    points.append((x, y))

                    if command in ("M", "m"):

                        command = "L" if command == "M" else "l"

                elif command in ("H", "h"):

                    x = float(tokens[i]); i += 1

                    if command == "h": x += current_x

                    current_x = x

                    points.append((current_x, current_y))

                elif command in ("V", "v"):

                    y = float(tokens[i]); i += 1

                    if command == "v": y += current_y

                    current_y = y

                    points.append((current_x, current_y))

                else:

                    i += 1

            except (ValueError, IndexError):

                i += 1



    if not points:

        return None



    # SVG transform functions are applied right-to-left: scale(translate(point)).

    transformed = [((x + tx) * sx, (y + ty) * sy) for x, y in points]

    xs = [point[0] for point in transformed]

    ys = [point[1] for point in transformed]

    return min(xs), min(ys), max(xs), max(ys)







def add_hole_callouts(root, view, geometry_group, holes, bounds=None):
    """
    Draw a diameter dimension directly across each circular hole opening.

    This deliberately does not group holes or place external leader labels.
    It is a first implementation of the ReportLab-style dimension shown
    in the user's example. Only holes viewed approximately along their
    axis are dimensioned.
    """
    if not holes or bounds is None:
        return

    direction = cq.Vector(*view["direction"]).normalized()

    # Parse the transform applied to CadQuery's geometry group.
    transform = geometry_group.get("transform", "")
    scale_match = re.search(
        r"scale\(\s*([-+0-9.eE]+)(?:[\s,]+([-+0-9.eE]+))?\s*\)",
        transform,
    )
    translate_match = re.search(
        r"translate\(\s*([-+0-9.eE]+)(?:[\s,]+([-+0-9.eE]+))?\s*\)",
        transform,
    )

    sx = float(scale_match.group(1)) if scale_match else 1.0
    sy = (
        float(scale_match.group(2) or scale_match.group(1))
        if scale_match else 1.0
    )
    tx = float(translate_match.group(1)) if translate_match else 0.0
    ty = (
        float(translate_match.group(2) or 0.0)
        if translate_match else 0.0
    )

    if abs(sx) < 1e-12 or abs(sy) < 1e-12:
        return

    # CadQuery's SVG projection basis: construct the same OCC axis system
    # used by the exporter for this projection direction.
    projection = gp_Ax2(
        gp_Pnt(),
        gp_Dir(direction.x, direction.y, direction.z)
    )
    occ_x = projection.XDirection()
    occ_y = projection.YDirection()
    svg_x_axis = cq.Vector(occ_x.X(), occ_x.Y(), occ_x.Z())
    svg_y_axis = cq.Vector(occ_y.X(), occ_y.Y(), occ_y.Z())

    def model_point_to_svg(point_dict):
        point = cq.Vector(
            float(point_dict["x"]),
            float(point_dict["y"]),
            float(point_dict["z"]),
        )
        # SVG group transform is scale(...) translate(...).
        raw_x = point.dot(svg_x_axis)
        raw_y = point.dot(svg_y_axis)
        return (raw_x + tx) * sx, (raw_y + ty) * sy

    def add_diameter_dimension(cx, cy, radius, label, angle_deg=45):
        angle = math.radians(angle_deg)
        dx = math.cos(angle)
        dy = math.sin(angle)

        x1 = cx - radius * dx
        y1 = cy - radius * dy
        x2 = cx + radius * dx
        y2 = cy + radius * dy

        # Dimension line through the projected circular opening.
        add_svg_line(root, x1, y1, x2, y2, width=0.75)

        # Filled arrowheads. Their tips touch the circumference and point
        # away from the centre, matching the supplied ReportLab example.
        arrow_len = max(3.0, min(5.0, radius * 0.35))
        arrow_half_width = max(1.4, min(2.2, radius * 0.16))

        def arrow_polygon(tip_x, tip_y, ux, uy):
            # Base lies inward from the tip; triangle points outward.
            base_x = tip_x - ux * arrow_len
            base_y = tip_y - uy * arrow_len
            px, py = -uy, ux
            p1 = (tip_x, tip_y)
            p2 = (
                base_x + px * arrow_half_width,
                base_y + py * arrow_half_width,
            )
            p3 = (
                base_x - px * arrow_half_width,
                base_y - py * arrow_half_width,
            )
            points = " ".join(f"{x:.3f},{y:.3f}" for x, y in (p1, p2, p3))
            ET.SubElement(
                root,
                f"{{{SVG_NS}}}polygon",
                {
                    "points": points,
                    "fill": "black",
                    "stroke": "black",
                    "stroke-width": "0.35",
                },
            )

        arrow_polygon(x2, y2, dx, dy)
        arrow_polygon(x1, y1, -dx, -dy)

        # White mask behind the diameter text.
        text_size = 7
        text_width = max(18, len(label) * text_size * 0.58)
        mask_height = 9
        ET.SubElement(
            root,
            f"{{{SVG_NS}}}rect",
            {
                "x": f"{cx - text_width / 2 - 1.5:.3f}",
                "y": f"{cy - mask_height / 2 - 1:.3f}",
                "width": f"{text_width + 3:.3f}",
                "height": f"{mask_height + 2:.3f}",
                "fill": "white",
                "stroke": "none",
            },
        )
        add_svg_text(
            root, cx, cy + 2.4, label,
            size=text_size, anchor="middle",
        )

    min_x, min_y, max_x, max_y = bounds
    view_width = max_x - min_x
    view_height = max_y - min_y
    if view_width <= 0 or view_height <= 0:
        return

    # Avoid drawing the same detected cylindrical face multiple times when
    # multiple candidates share the same opening centre and diameter.
    seen = set()

    for hole in holes:
        axis_data = hole.get("axis") or {}
        try:
            hole_axis = cq.Vector(
                float(axis_data["x"]),
                float(axis_data["y"]),
                float(axis_data["z"]),
            ).normalized()
            diameter = float(hole.get("diameter", 0))
        except (KeyError, TypeError, ValueError):
            continue

        if diameter <= 0:
            continue

        # A circular diameter can only be shown as a circle in a view
        # looking approximately along the hole axis.
        if abs(hole_axis.dot(direction)) < 0.985:
            continue

        # Prefer an opening endpoint. If the detector has no endpoints,
        # use its stored location as a fallback.
        anchor = hole.get("start_point") or hole.get("end_point") or hole.get("location")
        if not anchor:
            continue

        try:
            cx, cy = model_point_to_svg(anchor)
        except (KeyError, TypeError, ValueError):
            continue

        # SVG scale converts model millimetres into drawing units.
        radius = (diameter / 2.0) * abs(sx)
        if radius < 2.5:
            # Too small for legible internal arrows/text at this drawing scale.
            continue

        # Skip duplicate hole candidates at the same projected centre.
        duplicate_key = (
            round(cx, 1),
            round(cy, 1),
            round(diameter, 2),
        )
        if duplicate_key in seen:
            continue
        seen.add(duplicate_key)

        label = f"Ø{diameter:.2f}"
        add_diameter_dimension(cx, cy, radius, label, angle_deg=45)


def calculate_view_layout(shape, sheet_width=1300, sheet_height=800):

    """

    Calculate view canvas sizes and positions for a first-angle drawing.



    Arrangement:

        Right-side view | Front view | Isometric view

                              Top view below front



    Note: The scale is an estimate because CadQuery fits each exported

    projection to its SVG canvas independently.

    """



    # Support both CadQuery Workplane and Shape objects.

    solid = shape.val() if isinstance(shape, cq.Workplane) else shape

    bbox = solid.BoundingBox()



    length = bbox.xlen

    width = bbox.ylen

    height = bbox.zlen



    projected = {

        "RIGHT-SIDE VIEW": (width, height),

        "FRONT VIEW": (length, height),

        "TOP VIEW": (length, width),

        "ISOMETRIC VIEW": (

            (length + width) * 0.7071,

            height * 0.8165 + (length + width) * 0.4082,

        ),

    }



    # Drawing area reserved for views.

    area_left = 30

    area_top = 90

    area_width = 900

    area_height = 570



    # Canvas margins and spacing.

    margin_x = 30

    margin_y = 35

    gap = 25



    # The side, front, and isometric views occupy one row.

    row_width_model = sum(

        projected[name][0]

        for name in (

            "RIGHT-SIDE VIEW",

            "FRONT VIEW",

            "ISOMETRIC VIEW",

        )

    )



    row_height_model = max(

        projected[name][1]

        for name in (

            "RIGHT-SIDE VIEW",

            "FRONT VIEW",

            "ISOMETRIC VIEW",

        )

    )



    top_width_model, top_height_model = projected["TOP VIEW"]



    # Include canvas margins in the available-space calculation.

    required_width_model = (

        row_width_model

        + 3 * 2 * margin_x

        + 2 * gap

    )



    required_height_model = (

        row_height_model

        + 2 * margin_y

        + gap

        + top_height_model

        + 2 * margin_y

    )



    scale_x = area_width / required_width_model

    scale_y = area_height / required_height_model

    drawing_scale = min(scale_x, scale_y)



    views = []



    definitions = [

        ("RIGHT-SIDE VIEW", (1, 0, 0), (0, 0, 1)),

        ("FRONT VIEW", (0, 1, 0), (0, 0, 1)),

        ("TOP VIEW", (0, 0, 1), (0, 1, 0)),

        ("ISOMETRIC VIEW", (1, -1, 1), (0, 0, 1)),

    ]



    for name, direction, up in definitions:

        projected_width, projected_height = projected[name]



        canvas_width = math.ceil(

            projected_width * drawing_scale + 2 * margin_x

        )

        canvas_height = math.ceil(

            projected_height * drawing_scale + 2 * margin_y

        )



        views.append({

            "name": name,

            "direction": direction,

            "up": up,

            "projected_width": projected_width,

            "projected_height": projected_height,

            "width": max(100, canvas_width),

            "height": max(100, canvas_height),

        })



    side, front, top, iso = views



    # First-angle placement.

    row_y = area_top



    side["x"] = area_left

    side["y"] = row_y



    front["x"] = side["x"] + side["width"] + gap

    front["y"] = row_y



    iso["x"] = front["x"] + front["width"] + gap

    iso["y"] = row_y



    # Top view directly below the front view.

    top["x"] = (

        front["x"]

        + (front["width"] - top["width"]) // 2

    )



    top["y"] = (

        row_y

        + max(side["height"], front["height"], iso["height"])

        + gap

    )



    print(

        f"Model dimensions: "

        f"{length:.2f} x {width:.2f} x {height:.2f} mm"

    )

    print(f"Estimated layout scale: {drawing_scale:.3f}")



    return views, drawing_scale





def add_svg_text(root, x, y, text, size=13, bold=False, anchor="start"):

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

            "text-anchor": anchor,

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

            anchor="middle",

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

            anchor="middle",

        )


