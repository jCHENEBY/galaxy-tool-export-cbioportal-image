# galaxy-tool-export-cbioportal-image

## Overview
`galaxy-tool-export-cbioportal-image` is a Python-based tool designed to export data from Galaxy tools to cBioPortal images. This project aims to facilitate the integration and visualization of genomic data.

## Features
- Export data from Galaxy tools
- Generate cBioPortal-compatible images
- Easy integration with existing workflows
- Can be wrapped in a Galaxy server as a tool using the provided XML

## Installation
To install the necessary dependencies, run:
```bash
pip install -r requirements.txt
```

## Usage
To use the tool, execute the following command:
```bash
python export_cbioportal_image.py --input <input_file> --output <output_file>
```

### Arguments
- `--input`: Path to the input file
- `--output`: Path to the output file

## Galaxy Integration
This tool can be integrated into a Galaxy server using the provided XML file `export_cbioportal_image.xml`. The XML file defines the tool's interface and parameters for use within the Galaxy platform.
