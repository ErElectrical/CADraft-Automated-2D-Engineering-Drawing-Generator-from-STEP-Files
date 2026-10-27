from app.cad.step_reader import (
    get_face_adjacency,
    get_face_information,
    read_step,
    get_shape_information,
    detect_features,
    get_edge_information,
)
from app.drawing.generator import generate_drawing_pdf


def main():
    print(
        "CADraft is an automated CAD drawing generation system "
        "that analyzes STEP files, extracts geometric and feature "
        "information, generates orthographic projections and dimensions, "
        "and produces 2D engineering drawings in PDF format."
    )

    file_path = "sample_step/Part1.stp"

    # 1. Load the STEP file
    cad_shape = read_step(file_path)

    # 2. Extract model information
    information = get_shape_information(cad_shape)
    faces = get_face_information(cad_shape)
    edges = get_edge_information(cad_shape)
    adjacency = get_face_adjacency(cad_shape)

    # 3. Detect cylindrical features
    features = detect_features(faces)

    # 4. Generate PDF with model specifications and features
    output_pdfpath = "output/drawing1.pdf"

    generate_drawing_pdf(
        cad_shape,
        output_pdfpath,
        shape_information=information,
        face_information=faces,
        edge_information=edges,
        features=features,
    )

    print(f"Drawing generated successfully: {output_pdfpath}")

    # 5. Print detected features
    print("\n========== DETECTED FEATURES ==========")

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
