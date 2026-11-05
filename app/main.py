from app.cad.step_reader import (
    get_face_adjacency,
    get_face_information,
    read_step,
    get_shape_information,
    detect_features,
    get_edge_information,
    analyze_holes
)
from app.drawing.generator import generate_drawing_pdf
import time
import cadquery as cq

def measure_time(name, function, *args, **kwargs):
    start = time.perf_counter()

    result = function(*args, **kwargs)

    elapsed = time.perf_counter() - start

    print(f"{name}: {elapsed:.3f} seconds")

    return result


def main():
    print(
        "CADraft is an automated CAD drawing generation system "
        "that analyzes STEP files, extracts geometric and feature "
        "information, generates orthographic projections and dimensions, "
        "and produces 2D engineering drawings in PDF format."
    )

    file_path = "sample_step/Part1.stp"

    

    # 1. Load the STEP file
    
    cad_shape =  measure_time("STEP file loading", read_step, file_path)


    # 2. Extract model information
    

    information = measure_time("Shape information extraction", get_shape_information, cad_shape)

    #faces = get_face_information(cad_shape)
    faces = measure_time("Face information extraction", get_face_information, cad_shape)

    cylinderical_faces = [face for face in faces if face["type"].lower() == "cylinder"]
    print(f"Detected {len(cylinderical_faces)} cylindrical faces.")

    #edges = get_edge_information(cad_shape)
    edges = measure_time("Edge information extraction", get_edge_information, cad_shape)

    

    #adjacency = measure_time("Face adjacency extraction", get_face_adjacency, cad_shape)

    # 3. Detect cylindrical features
      

    features = measure_time("Feature detection", detect_features, cad_shape, faces)

    # 4. Analyze complete hole features
    holes = measure_time("Hole analysis", analyze_holes, cad_shape, faces, features)
    print("\n========== HOLE ANALYSIS ==========")
    
    for hole in holes:
    
        print(f"\nHole ID: {hole['hole_id']}")
        print(f"Diameter: {hole['diameter']:.3f} mm")
        print(f"Cylindrical Depth: {hole['cylindrical_depth']:.3f} mm")
        print(f"Classification: {hole['hole_type']}")
        print(f"Face IDs: {hole['face_ids']}")

    # 4. Generate PDF with model specifications and features
    output_pdfpath = "output/Part1_drawing.pdf"


    measure_time("Drawing generation",
        generate_drawing_pdf,
        cad_shape,  
        output_pdfpath,
        shape_information=information,
        face_information=faces,
        edge_information=edges,
        features=features,
        holes=holes
    )


    
    # generate_drawing_pdf(
    #     cad_shape,
    #     output_pdfpath,
    #     shape_information=information,
    #     face_information=faces,
    #     edge_information=edges,
    #     features=features,
    #     holes=holes
    # )

    print(f"Drawing generated successfully: {output_pdfpath}")

    # 5. Print detected features
    print("\n========== DETECTED FEATURES ==========")

    # print("\n========== CYLINDER FACE TEST ==========")

    # # Get cylindrical face information
    # cylinder_faces = [
    #     face for face in faces
    #     if face["type"] == "CYLINDER"
    # ]

    # if cylinder_faces:

    #     test_face_info = cylinder_faces[0]

    #     # Get the actual CadQuery face using its ID
    #     raw_faces = cad_shape.val().Faces() if isinstance(cad_shape, cq.Workplane) else cad_shape.Faces()

    #     test_face = raw_faces[test_face_info["id"] - 1]

    #     # Get UV bounds
    #     u_min, u_max, v_min, v_max = test_face._uvBounds()

    #     print("U Min:", u_min)
    #     print("U Max:", u_max)
    #     print("V Min:", v_min)
    #     print("V Max:", v_max)

    #     start_point = test_face.positionAt(
    #         u_min, v_min
    #     )

    #     end_point = test_face.positionAt(
    #         u_min, v_max
    #     )

    #     print("Start:", start_point)
    #     print("End:", end_point)

    #     depth = start_point.sub(end_point).Length

    #     print("Axial Length:", depth)

    # else:
    #     print("No cylindrical faces found.")


    for feature in features:
        print(f"Feature Type: {feature.feature_type}")
        print(f"Parameters: {feature.parameters}")
        print(f"Face IDs: {feature.face_ids}")

    # 6. Print overall shape information
    print("\n========== SHAPE INFORMATION ==========")

    for key, value in information.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
