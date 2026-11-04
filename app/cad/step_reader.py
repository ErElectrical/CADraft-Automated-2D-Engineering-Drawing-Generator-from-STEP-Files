import cadquery as cq
from app.Model.FaceFeatures import Feature as Feature
import math


def read_step(file_path):
    """
    Read a STEP/STP file and return the CAD shape.
    """
    result = cq.importers.importStep(file_path)

    return result


def get_shape_information(shape):
    """
    Extract basic information from the loaded CAD shape.
    """

    solids = shape.solids().vals()
    faces = shape.faces().vals()
    edges = shape.edges().vals()

    # Get bounding box
    bounding_box = shape.val().BoundingBox()

    #Get information of faces

    face_information = []

    for index, face in enumerate(faces, start=1):

        information = get_face_geometry(face)

        information["id"] = index

        face_information.append(information)




    return {
        "solids": len(solids),
        "faces": len(faces),
        "edges": len(edges),
        "length": bounding_box.xlen,
        "width": bounding_box.ylen,
        "height": bounding_box.zlen,
        "center_x": bounding_box.center.x,
        "center_y": bounding_box.center.y,
        "center_z": bounding_box.center.z,
    }


def get_face_information(shape):
    """
    Extract detailed information about every face,
    including its associated edge IDs.
    """

    faces = shape.faces().vals()
    edges = shape.edges().vals()

    # Build edge-to-ID lookup once
    edge_lookup = {
        edge.hashCode(): index
        for index, edge in enumerate(edges, start=1)
    }

    face_information = []

    for index, face in enumerate(faces, start=1):

        information = get_face_geometry(face)

        information["id"] = index

        center = face.Center()

        information["center"] = {
            "x": center.x,
            "y": center.y,
            "z": center.z
        }

        bbox = face.BoundingBox()

        information["bounding_box"] = {
            "length": bbox.xlen,
            "width": bbox.ylen,
            "height": bbox.zlen
        }

        # Find associated edge IDs
        edge_ids = []

        for face_edge in face.Edges():

            edge_id = edge_lookup.get(face_edge.hashCode())

            if edge_id is not None:
                edge_ids.append(edge_id)

        information["edge_ids"] = edge_ids

        face_information.append(information)

    return face_information

def get_face_geometry(face):

    geometry_type = face.geomType()

    result = {
        "type": geometry_type,
        "area": face.Area(),
    }

    # Get the underlying Open CASCADE surface
    surface = face._geomAdaptor()

    if geometry_type == "PLANE":

        plane = surface

        result["normal"] = {
            "x": plane.Axis().Direction().X(),
            "y": plane.Axis().Direction().Y(),
            "z": plane.Axis().Direction().Z()
        }

        result["location"] = {
            "x": plane.Location().X(),
            "y": plane.Location().Y(),
            "z": plane.Location().Z()
        }

    elif geometry_type == "CYLINDER":

        cylinder = surface

        result["radius"] = cylinder.Radius()

        result["axis"] = {
            "x": cylinder.Axis().Direction().X(),
            "y": cylinder.Axis().Direction().Y(),
            "z": cylinder.Axis().Direction().Z()
        }

        result["location"] = {
            "x": cylinder.Location().X(),
            "y": cylinder.Location().Y(),
            "z": cylinder.Location().Z()
        }

    return result


def detect_features(shape, faces, tolerance=0.01):
    """
    Detect and classify cylindrical surfaces.

    The first classification stage distinguishes:
        - Internal cylindrical surfaces (hole candidates)
        - External cylindrical surfaces (boss candidates)

    Through-hole and blind-hole classification is a later stage.
    """

    # Support Workplane and Shape objects
    solid = shape.val() if isinstance(shape, cq.Workplane) else shape

    raw_faces = solid.Faces()

    grouped_features = {}

    def rounded(value):
        return round(value / tolerance) * tolerance

    for face_info in faces:

        if face_info["type"] != "CYLINDER":
            continue

        face_id = face_info["id"]

        if face_id < 1 or face_id > len(raw_faces):
            continue

        raw_face = raw_faces[face_id - 1]

        radius = face_info["radius"]
        axis = face_info["axis"]
        location = face_info["location"]

        # Normalize axis
        axis_length = math.sqrt(
            axis["x"]**2 +
            axis["y"]**2 +
            axis["z"]**2
        )

        if axis_length < 1e-9:
            continue

        ax = axis["x"] / axis_length
        ay = axis["y"] / axis_length
        az = axis["z"] / axis_length

        # Normalize opposite directions
        for component in (ax, ay, az):
            if abs(component) > tolerance:
                if component < 0:
                    ax, ay, az = -ax, -ay, -az
                break

        normalized_axis = {
            "x": ax,
            "y": ay,
            "z": az
        }

        # Classify the cylindrical surface
        classification = classify_cylindrical_face(
            solid,
            raw_face,
            radius,
            normalized_axis,
            location
        )

        if classification == "UNKNOWN":
            continue

        # Calculate a representative point on the cylinder axis
        dot = (
            location["x"] * ax +
            location["y"] * ay +
            location["z"] * az
        )

        px = location["x"] - dot * ax
        py = location["y"] - dot * ay
        pz = location["z"] - dot * az

        key = (
            classification,
            rounded(radius),
            rounded(ax),
            rounded(ay),
            rounded(az),
            rounded(px),
            rounded(py),
            rounded(pz)
        )

        if key not in grouped_features:

            feature_type = (
                "CYLINDRICAL_HOLE_CANDIDATE"
                if classification == "HOLE_CANDIDATE"
                else "CYLINDRICAL_BOSS_CANDIDATE"
            )

            grouped_features[key] = {
                "feature_type": feature_type,
                "parameters": {
                    "radius": radius,
                    "diameter": radius * 2,
                    "axis": normalized_axis,
                    "location": location.copy()
                },
                "face_ids": [],
                "confidence": 0.90
            }

        grouped_features[key]["face_ids"].append(face_id)

    # Convert grouped results to Feature objects
    features = []

    for item in grouped_features.values():

        features.append(
            Feature(
                feature_type=item["feature_type"],
                parameters=item["parameters"],
                face_ids=item["face_ids"],
                confidence=item["confidence"]
            )
        )

    return features


def get_edge_information(shape):
    """
    Extract geometric information about every edge.
    """

    edges = shape.edges().vals()
    edge_information = []

    for index, edge in enumerate(edges, start=1):

        geometry_type = edge.geomType()
        center = edge.Center()
        bbox = edge.BoundingBox()

        start = edge.startPoint()
        end = edge.endPoint()

        information = {
            "id": index,
            "type": geometry_type,
            "length": edge.Length(),

            "center": {
                "x": center.x,
                "y": center.y,
                "z": center.z
            },

            "start_point": {
                "x": start.x,
                "y": start.y,
                "z": start.z
            },

            "end_point": {
                "x": end.x,
                "y": end.y,
                "z": end.z
            },

            "bounding_box": {
                "length": bbox.xlen,
                "width": bbox.ylen,
                "height": bbox.zlen
            }
        }

        # Additional properties for circular edges
        if geometry_type == "CIRCLE":
            information["radius"] = edge.radius()

            arc_center = edge.arcCenter()

            information["circle_center"] = {
                "x": arc_center.x,
                "y": arc_center.y,
                "z": arc_center.z
            }

        edge_information.append(information)

    return edge_information

def get_face_adjacency(shape):
    """
    Find which faces share each edge.

    Returns:
        A list of edges and the IDs of adjacent faces.
    """

    faces = shape.faces().vals()
    edges = shape.edges().vals()

    # Assign a stable face ID for this analysis run.
    face_ids = {
        index: face
        for index, face in enumerate(faces, start=1)
    }

    adjacency = []

    for edge_index, edge in enumerate(edges, start=1):

        adjacent_face_ids = []

        for face_id, face in face_ids.items():

            # Check whether this face contains the same topological edge.
            for face_edge in face.Edges():

                if edge.isSame(face_edge):
                    adjacent_face_ids.append(face_id)
                    break

        adjacency.append({
            "edge_id": edge_index,
            "adjacent_faces": adjacent_face_ids,
            "face_count": len(adjacent_face_ids)
        })

    return adjacency





def classify_cylindrical_face(solid, face, radius, axis, location):
    """
    Classify a cylindrical face as an internal hole or external boss.

    Uses a point in the interior of the cylindrical face rather
    than a boundary vertex.
    """

    ax, ay, az = axis["x"], axis["y"], axis["z"]

    # Get a point near the middle of the cylindrical face
    u_min, u_max, v_min, v_max = face._uvBounds()

    u_mid = (u_min + u_max) / 2
    v_mid = (v_min + v_max) / 2

    center = face.positionAt(u_mid, v_mid)

    # Vector from cylinder axis to the selected surface point
    dx = center.x - location["x"]
    dy = center.y - location["y"]
    dz = center.z - location["z"]

    # Remove axial component
    dot = dx * ax + dy * ay + dz * az

    rx = dx - dot * ax
    ry = dy - dot * ay
    rz = dz - dot * az

    radial_length = math.sqrt(rx**2 + ry**2 + rz**2)

    if radial_length < 1e-9:
        return "UNKNOWN"

    rx /= radial_length
    ry /= radial_length
    rz /= radial_length

    # Sampling distance
    epsilon = min(max(radius * 0.005, 0.001), 0.02)

    # Point radially outside the cylinder
    outside_point = cq.Vector(
        center.x + rx * epsilon,
        center.y + ry * epsilon,
        center.z + rz * epsilon
    )

    # Point radially inside the cylinder
    inside_point = cq.Vector(
        center.x - rx * epsilon,
        center.y - ry * epsilon,
        center.z - rz * epsilon
    )

    outside_material = solid.isInside(outside_point, 1e-6)
    inside_material = solid.isInside(inside_point, 1e-6)

    # Internal cylindrical surface: material is outside the radius
    if outside_material and not inside_material:
        return "HOLE_CANDIDATE"

    # External cylindrical surface: material is inside the radius
    if inside_material and not outside_material:
        return "BOSS_CANDIDATE"

    return "UNKNOWN"






def analyze_holes(shape, faces, features, probe_distance=1.0,
                  tolerance=0.01):

    raw_faces = (
        shape.val().Faces()
        if isinstance(shape, cq.Workplane)
        else shape.Faces()
    )

    # Only consider features already identified as hole candidates
    hole_features = [
        feature for feature in features
        if "HOLE" in feature.feature_type.upper()
    ]

    results = []

    def get_vector(data):
        return cq.Vector(
            data["x"],
            data["y"],
            data["z"]
        )

    def same_cylinder(feature_a, feature_b):

        params_a = feature_a.parameters
        params_b = feature_b.parameters

        radius_a = params_a["radius"]
        radius_b = params_b["radius"]

        if abs(radius_a - radius_b) > tolerance:
            return False

        axis_a = get_vector(params_a["axis"]).normalized()
        axis_b = get_vector(params_b["axis"]).normalized()

        # Check whether axes are parallel
        if abs(axis_a.dot(axis_b)) < 0.9999:
            return False

        location_a = get_vector(params_a["location"])
        location_b = get_vector(params_b["location"])

        # Check whether both axes lie on the same line
        distance = (
            location_b.sub(location_a)
            .cross(axis_a)
            .Length
        )

        return distance <= tolerance

    # Group coaxial cylindrical features
    groups = []

    for feature in hole_features:

        matched_group = None

        for group in groups:
            if same_cylinder(group[0], feature):
                matched_group = group
                break

        if matched_group is None:
            groups.append([feature])
        else:
            matched_group.append(feature)

    # Analyze each grouped hole
    for index, group in enumerate(groups, start=1):

        first = group[0]
        params = first.parameters

        radius = params["radius"]
        diameter = radius * 2

        axis = get_vector(params["axis"]).normalized()
        location = get_vector(params["location"])

        axial_values = []

        face_ids = []

        # Calculate axial extent of every cylindrical face
        for feature in group:

            for face_id in feature.face_ids:

                if face_id in face_ids:
                    continue

                face_ids.append(face_id)

                face = raw_faces[face_id - 1]

                u_min, u_max, v_min, v_max = face._uvBounds()

                u_mid = (u_min + u_max) / 2

                start = face.positionAt(u_mid, v_min)
                end = face.positionAt(u_mid, v_max)

                start_projection = (
                    start.sub(location).dot(axis)
                )

                end_projection = (
                    end.sub(location).dot(axis)
                )

                axial_values.extend([
                    start_projection,
                    end_projection
                ])

        if not axial_values:
            continue

        axial_min = min(axial_values)
        axial_max = max(axial_values)

        cylindrical_depth = axial_max - axial_min

        start_point = location.add(
            axis.multiply(axial_min)
        )

        end_point = location.add(
            axis.multiply(axial_max)
        )

        # Build two perpendicular vectors around the hole axis
        reference = (
            cq.Vector(1, 0, 0)
            if abs(axis.x) < 0.9
            else cq.Vector(0, 1, 0)
        )

        radial_1 = axis.cross(reference).normalized()
        radial_2 = axis.cross(radial_1).normalized()

        def check_opening(point, direction):

            # Sample eight points around the hole opening
            outside_count = 0

            sample_radius = radius * 0.8

            for i in range(8):

                angle = 2 * math.pi * i / 8

                radial = (
                    radial_1.multiply(math.cos(angle))
                    .add(radial_2.multiply(math.sin(angle)))
                )

                sample_point = (
                    point
                    .add(direction.multiply(probe_distance))
                    .add(radial.multiply(sample_radius))
                )

               
                solid = (
                    shape.val()
                    if isinstance(shape, cq.Workplane)
                    else shape
                )

                if not solid.isInside(sample_point, tolerance):
                    outside_count += 1

            return outside_count >= 7

        # Check both axial ends
        start_open = check_opening(start_point, axis.multiply(-1))

        end_open = check_opening(end_point, axis)

        if start_open and end_open:
            hole_type = "LIKELY_THROUGH"

        elif start_open != end_open:
            hole_type = "LIKELY_BLIND"

        else:
            hole_type = "UNKNOWN"

        results.append({

            "hole_id": index,

            "diameter": diameter,
            "radius": radius,

            "axis": {
                "x": axis.x,
                "y": axis.y,
                "z": axis.z
            },

            "location": {
                "x": location.x,
                "y": location.y,
                "z": location.z
            },

            "start_point": {
                "x": start_point.x,
                "y": start_point.y,
                "z": start_point.z
            },

            "end_point": {
                "x": end_point.x,
                "y": end_point.y,
                "z": end_point.z
            },

            "cylindrical_depth": cylindrical_depth,

            "hole_type": hole_type,

            "face_ids": face_ids

        })

    return results





