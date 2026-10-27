import cadquery as cq
from app.Model.FaceFeatures import Feature as Feature


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
    Extract detailed information about every face.
    """

    faces = shape.faces().vals()

    face_information = []

    for index, face in enumerate(faces, start=1):

        information = get_face_geometry(face)

        # Add face ID
        information["id"] = index

        # Add center
        center = face.Center()

        information["center"] = {
            "x": center.x,
            "y": center.y,
            "z": center.z
        }

        # Add bounding box
        bbox = face.BoundingBox()

        information["bounding_box"] = {
            "length": bbox.xlen,
            "width": bbox.ylen,
            "height": bbox.zlen
        }

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

def detect_features(faces, tolerance=0.01):
    """
    Detect unique cylindrical surfaces.

    Multiple faces representing the same cylindrical surface
    are grouped into one feature.

    Note:
        A cylindrical surface is not automatically a hole.
        Additional geometric analysis is needed to distinguish
        holes from external cylindrical features.
    """
    features = []
    grouped_features = {}

    def rounded(value):
        return round(value / tolerance) * tolerance

    for face in faces:
        if face["type"] != "CYLINDER":
            continue

        radius = face["radius"]
        axis = face["axis"]
        location = face["location"]

        # Normalize the axis direction.
        axis_length = (
            axis["x"] ** 2
            + axis["y"] ** 2
            + axis["z"] ** 2
        ) ** 0.5

        if axis_length == 0:
            continue

        ax = axis["x"] / axis_length
        ay = axis["y"] / axis_length
        az = axis["z"] / axis_length

        # Make opposite directions use the same orientation.
        for component in (ax, ay, az):
            if abs(component) > tolerance:
                if component < 0:
                    ax, ay, az = -ax, -ay, -az
                break

        # Calculate a representative point for the cylinder axis.
        # Points along the same axis produce the same perpendicular
        # location, even if their original coordinates differ.
        dot = (
            location["x"] * ax
            + location["y"] * ay
            + location["z"] * az
        )

        px = location["x"] - dot * ax
        py = location["y"] - dot * ay
        pz = location["z"] - dot * az

        key = (
            rounded(radius),
            rounded(ax),
            rounded(ay),
            rounded(az),
            rounded(px),
            rounded(py),
            rounded(pz),
        )

        if key not in grouped_features:
            grouped_features[key] = {
                "feature_type": "CYLINDRICAL_FEATURE",
                "parameters": {
                    "radius": radius,
                    "diameter": radius * 2,
                    "axis": {
                        "x": ax,
                        "y": ay,
                        "z": az,
                    },
                    "location": {
                        "x": location["x"],
                        "y": location["y"],
                        "z": location["z"],
                    },
                },
                "face_ids": [],
            }

        grouped_features[key]["face_ids"].append(face["id"])

    # Convert grouped results to your existing Feature model.
    for item in grouped_features.values():
        features.append(
            Feature(
                feature_type=item["feature_type"],
                parameters=item["parameters"],
                face_ids=item["face_ids"],
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
