# CADraft – Automated STEP to 2D Engineering Drawing Generator

CADraft is a Python-based engineering automation project designed to convert 3D STEP models into 2D engineering drawing PDFs.

The application uses **CadQuery and OpenCascade** to process 3D CAD geometry, extract geometric information, analyze faces and edges, identify cylindrical feature candidates, and generate orthographic engineering views.

The goal is to reduce repetitive engineering drawing work through automated geometry analysis and drawing generation.

## Project Overview

CADraft follows a geometry-processing and drawing-generation workflow:

```text
3D STEP File
     |
     v
STEP File Import
     |
     v
3D Geometry Analysis
     |
     v
Face & Edge Extraction
     |
     v
Geometric Feature Detection
     |
     v
Orthographic View Generation
     |
     v
Dimension & Annotation Placement
     |
     v
Engineering Drawing PDF
```

## Features

### 1. STEP File Processing
- Import 3D STEP models.
- Process solid geometry using CadQuery.
- Extract solid, face and edge information.
- Calculate bounding-box dimensions and model center.

### 2. Geometric Analysis
- Identify planar and cylindrical surfaces.
- Extract face areas, normals, locations and geometric properties.
- Extract edge types, lengths and coordinates.
- Generate face adjacency information.

### 3. Basic Feature Recognition
- Identify cylindrical surface groups.
- Classify cylindrical hole and boss candidates using geometric analysis.
- Analyze cylindrical hole candidates.
- Estimate whether detected holes are likely through or blind.

*Feature recognition is currently heuristic-based and is not intended to infer every manufacturing feature automatically.*

### 4. Engineering Drawing Generation
- Generate front view.
- Generate top view.
- Generate right-side view.
- Generate isometric view.
- Add overall model dimensions.
- Generate supported cylindrical feature callouts.
- Compose drawing sheets with borders and title blocks.

### 5. PDF Export
- Generate SVG-based engineering drawing layouts.
- Convert SVG drawings into PDF documents.
- Include part specifications and geometric information.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Core development |
| CadQuery | CAD geometry processing |
| OpenCascade | Geometric and topological operations |
| SVG | Drawing composition |
| svglib | SVG to ReportLab graphics conversion |
| ReportLab | PDF generation |

## Project Structure

```text
CADraft/
│
├── step_reader.py
│   └── STEP import and geometry extraction
│
├── FaceFeatures.py
│   └── Geometric feature data model
│
├── analyzer.py
│   └── Feature analysis and processing orchestration
│
├── generator.py
│   └── Engineering drawing and PDF generation
│
├── sample_step/
│   └── Sample STEP models
│
├── output/
│   └── Generated engineering drawings
│
├── requirements.txt
│
└── README.md
```

*The structure above describes the current planned organization; adjust filenames and folders to match the actual repository before publishing.*

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/CADraft.git
cd CADraft
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install cadquery svglib reportlab
```

If a `requirements.txt` file is available:

```bash
pip install -r requirements.txt
```

## Usage

The typical processing workflow is:

1. Provide a valid STEP file.
2. Import the model using the STEP reader.
3. Extract geometric and topological information.
4. Perform feature analysis.
5. Generate orthographic projections.
6. Export the engineering drawing as a PDF.

The exact execution command depends on the current application entry point.

## Example Output

An example CADraft-generated engineering drawing contains:

- Front view
- Top view
- Right-side view
- Isometric view
- Overall dimensions
- Cylindrical feature information
- Part specifications
- Engineering drawing title block

## Current Development Status

**Project status: Prototype / Active Development**

Implemented capabilities include:

- STEP file importing.
- Solid, face and edge extraction.
- Bounding-box dimension calculation.
- Planar and cylindrical surface analysis.
- Basic cylindrical feature detection.
- Orthographic and isometric view generation.
- Overall dimension placement.
- Supported cylindrical feature callouts.
- PDF drawing generation.

## Future Development

Planned improvements include:

- Advanced geometric feature recognition.
- Improved hole, pocket, slot and chamfer detection.
- More reliable automatic dimensioning.
- Improved dimension placement and annotation layout.
- Engineering drawing standard support.
- Better handling of complex mechanical components.
- Improved drawing validation.

## Project Objective

CADraft explores the use of computational geometry and Python automation to bridge the gap between 3D CAD models and 2D engineering documentation.

The long-term objective is to develop a practical automated engineering drawing generation system that can process mechanical components and produce structured, readable technical drawings.

---

**Developed with Python, CadQuery and OpenCascade.**
