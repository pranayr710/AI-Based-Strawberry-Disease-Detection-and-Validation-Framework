# 🍓 AI-Based Strawberry Disease Detection and Validation Framework

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green.svg)
![Deep Learning](https://img.shields.io/badge/AI-YOLOv8-red.svg)

A high-precision software suite designed for the automated detection, classification, and validation of strawberry pathologies. This framework integrates state-of-the-art Computer Vision models with a robust human-in-the-loop validation interface to ensure 100% accuracy in agricultural datasets.

## 📋 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technical Architecture](#-technical-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [License](#-license)

## 🌟 Overview
In modern agriculture, early disease detection is critical. This framework provides a dual-approach solution:
1. **Automated Analysis**: Uses YOLOv8-segmentation to identify leaf damage and disease symptoms.
2. **Quality Assurance Interface**: A specialized PyQt5 application for human experts to verify, refine, and "sign off" on AI-generated labels across massive datasets.

## ✨ Key Features

### 🖥️ Advanced Annotation GUI
- **Multi-Label Management**: Simultaneously apply or remove multiple pathology tags (e.g., *Healthy, Powdery Mildew, Angular Leaf Spot*).
- **Bulk Refinement**: Copy labels from a "source" patch to hundreds of "target" images with a single click.
- **Smart Filtering**: Search images by specific combinations of labels or verification status.
- **Verification Workflow**: Integrated "Signed" status tracking to monitor dataset completion progress.

### 🧠 AI & Image Processing
- **High-Res Segmentation**: YOLOv8l-seg integration for pixel-perfect leaf and lesion masking.
- **Automated Extraction**: Specialized pipelines for cropping image patches based on model detections.
- **Leaf Separation**: Advanced leaf segmentation to isolate individual plant units for granular analysis.

## 🏗️ Technical Architecture

### Tech Stack
- **Language**: Python 3.10+
- **Frontend GUI**: PyQt5 (Custom Dark Mode Interface)
- **Deep Learning**: Ultralytics YOLOv8 (Segmentation & Detection)
- **Data Handling**: Pandas & NumPy
- **Image Processing**: OpenCV & Pillow

### Dataset Pipeline
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Raw Field   │      │ AI Detection │      │ Patch        │
│  Images      │ ───► │ (YOLOv8)     │ ───► │ Extraction   │
└──────────────┘      └──────────────┘      └──────┬───────┘
                                                   │
                                                   ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Dataset      │      │ Human        │      │ Expert       │
│ Signed/Ready │ ◄─── │ Validation   │ ◄─── │ Mapping      │
└──────────────┘      └──────────────┘      └──────────────┘
```

## 🚀 Installation

### Prerequisites
- Python 3.10.x
- CUDA Toolkit (Recommended for GPU acceleration)

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/pranayr710/AI-Based-Strawberry-Disease-Detection-and-Validation-Framework.git
   cd AI-Based-Strawberry-Disease-Detection-and-Validation-Framework
   ```

2. **Install dependencies**
   ```bash
   pip install PyQt5 pandas opencv-python ultralytics pillow
   ```

## 💻 Usage

### Launching the Validation Tool
```bash
cd Label-Checking-Tool-main
python screen.py
```

### Main Tool Workflow
1. **Search**: Use the top search bar or label filters to find specific patches.
2. **Annotate**: Click on the label buttons to add/remove disease categories.
3. **Bulk Edit**: Select a source image (Green), multiple targets (Red), and hit **Confirm Multi-Label Change**.
4. **Sign Off**: Click **CONFIRM** to save changes and mark the image as verified.

## 📁 Project Structure
```
AI-Based-Strawberry-Disease-Detection.../
├── Label-Checking-Tool-main/   # Main GUI Application
│   ├── screen.py               # Main Entry Point
│   ├── image_panel.py          # Custom Image Viewer
│   ├── btn_grid.py             # Label Selection Logic
│   └── ...                     # Supporting GUI Components
├── extraction_check.py          # Patch extraction verification
├── count_labels.py             # Statistical analysis scripts
└── .gitignore                  # Data exclusion rules
```

## 📄 License
This project is licensed under the MIT License.

## 📞 Contact
**Developer**: Pranay R  
**GitHub**: [@pranayr710](https://github.com/pranayr710)

---
*Developed for efficient agricultural AI training and data validation.*
