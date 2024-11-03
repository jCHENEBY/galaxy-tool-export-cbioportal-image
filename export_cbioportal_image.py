import argparse
import os
from urllib.parse import urlparse, urlunparse

import requests
import pandas as pd


def make_meta_resource(study_id: str, data_file: str, type: str) -> str:
    return f"cancer_study_identifier: {study_id}\nresource_type: {type}\ndata_filename: {data_file}\n"


def make_data_resource_definition(display_name: str, description: str, resource_type: str = "PATIENT",
                                  resource_id: str = "CLONAL_CLUSTER_PLOT") -> str:
    header = [
        "RESOURCE_ID",
        "DISPLAY_NAME",
        "RESOURCE_TYPE",
        "DESCRIPTION",
        "OPEN_BY_DEFAULT",
        "PRIORITY"
    ]

    # For now start from empty lists
    list_display_name = []
    list_display_name.append(display_name)

    list_description = []
    list_description.append(description)

    list_resource_type = []
    list_resource_type.append(resource_type)

    list_resource_id = []
    list_resource_id.append(resource_id)

    # Check if all lists have the same length
    if len(set(map(len, [list_display_name, list_description, list_resource_type, list_resource_id]))) != 1:
        raise ValueError("All lists must have the same length")

    # Create the data resource definition
    file_content = "\t".join(header) + "\n"
    for i in range(len(list_display_name)):
        file_content += "\t".join(
            [list_resource_id[i], list_display_name[i], list_resource_type[i], list_description[i], "false",
             "0"]) + "\n"

    return file_content


def make_data_resource_patient(patient_id: str, resource_id: str, url: str) -> str:
    header = [
        "PATIENT_ID",
        "RESOURCE_ID",
        "URL"
    ]

    # For now start from empty lists
    list_patient_id = []
    list_patient_id.append(patient_id)

    list_resource_id = []
    list_resource_id.append(resource_id)

    list_url = []
    list_url.append(url)

    # Check if all lists have the same length
    if len(set(map(len, [list_patient_id, list_resource_id, list_url]))) != 1:
        raise ValueError("All lists must have the same length")

    # Create the data resource definition
    file_content = "\t".join(header) + "\n"
    for i in range(len(list_patient_id)):
        file_content += "\t".join([list_patient_id[i], list_resource_id[i], list_url[i]]) + "\n"

    return file_content


def export_image_resource_to_cbioportal(data_definition_content: str, data_patient_content: str,
                                        meta_definition_content: str, meta_patient_content: str,
                                        study_id: str) -> requests.Response:
    load_resource_endpoint = os.getenv('CBIOPORTAL_LOAD_RESOURCE_ENDPOINT')
    if not load_resource_endpoint:
        raise ValueError("CBIOPORTAL_LOAD_RESOURCE_ENDPOINT environment variable is not set")


    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "dataDefinitionContent": data_definition_content,
        "metaDefinitionContent": meta_definition_content,
        "dataPatientContent": data_patient_content,
        "metaPatientContent": meta_patient_content,
        "studyId": study_id,
    }

    response_request = requests.post(load_resource_endpoint, headers=headers, json=data)

    return response_request


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PyClone data to cBioPortal timeline format")
    parser.add_argument("-i", "--input_image", required=True, help="Input image file from history")
    parser.add_argument("-s", "--study_id", required=True, help="Study ID")
    parser.add_argument("-c", "--case_id", required=True, help="Case ID")
    parser.add_argument("-mdo", "--meta_definition_output", required=True,
                        help="Output resource definition meta file path")
    parser.add_argument("-ddo", "--data_definition_output", required=True,
                        help="Output resource definition data file path")
    parser.add_argument("-mdp", "--meta_patient_output", required=True, help="Output resource patient meta file path")
    parser.add_argument("-ddp", "--data_patient_output", required=True, help="Output resource patient data file path")
    parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing image URL")
    parser.add_argument("-n", "--name", help="Name of the image")

    args = parser.parse_args()

    name_meta_resource_definition = "meta_resource_definition.txt"
    name_data_resource_definition = "data_resource_definition.txt"
    name_meta_resource_patient = "meta_resource_patient.txt"
    name_data_resource_patient = "data_resource_patient.txt"

    # Set environment variables
    load_image_endpoint = os.getenv('UPLOAD_IMAGE_ENDPOINT')
    if not load_image_endpoint:
        raise ValueError("UPLOAD_IMAGE_ENDPOINT environment variable is not set")

    image_base_url = os.getenv('IMAGE_BASE_URL')


    # replace file name with name argument (keep path before file name)
    file_name = args.input_image
    if args.name.strip() != "":
        file_name = os.path.join(os.path.dirname(args.input_image), args.name)
    print(f"File name: {file_name}")


    # Upload image
    with open(args.input_image, "rb") as image_file:
        files = {'file': (file_name, image_file, 'image/png')}
        data = {'overwrite': 'true'}
        response = requests.post(load_image_endpoint, files=files, data=data)


    if response.status_code != 200:
        raise Exception(f"Error: Received status code {response.status_code}: '{response.json().get('detail')}'")
    image_url = response.json().get('url')

    if image_base_url != "":
        parsed_base_url = urlparse(image_base_url)
        parsed_final_url = urlparse(image_url)

        # Check if the base URLs are different
        if parsed_base_url.netloc != parsed_final_url.netloc:
            # Replace the base URL of final_url with base_url
            image_url = urlunparse(parsed_base_url._replace(path=parsed_final_url.path))


    print(f"Image URL: {image_url}")

    # Make files content
    resource_id = "CLONAL_CLUSTER_PLOT"

    content_meta_resource_definition = make_meta_resource(study_id=args.study_id,
                                                          data_file=name_data_resource_definition,
                                                          type="DEFINITION")
    content_meta_resource_patient = make_meta_resource(study_id=args.study_id,
                                                       data_file=name_data_resource_patient,
                                                       type="PATIENT")

    content_data_resource_definition = make_data_resource_definition(
        display_name=f"Clonal Cluster Plot",
        description=f"Clone frequency plot for clonal clusters from PyClone-VI",
        resource_type="PATIENT",
        resource_id=resource_id)

    content_data_resource_patient = make_data_resource_patient(
        patient_id=args.case_id,
        resource_id=resource_id,
        url=image_url)


    response = export_image_resource_to_cbioportal(data_definition_content=content_data_resource_definition,
                                                   data_patient_content=content_data_resource_patient,
                                                   meta_definition_content=content_meta_resource_definition,
                                                   meta_patient_content=content_meta_resource_patient,
                                                   study_id=args.study_id)

    with open(args.meta_definition_output, 'w') as f:
        f.write(content_meta_resource_definition)

    with open(args.data_definition_output, 'w') as f:
        f.write(content_data_resource_definition)

    with open(args.meta_patient_output, 'w') as f:
        f.write(content_meta_resource_patient)

    with open(args.data_patient_output, 'w') as f:
        f.write(content_data_resource_patient)
