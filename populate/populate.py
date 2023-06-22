import glob
import os
import time
from typing import List

import requests
import json


def create_dataset_endpoint(form_data: json, filenames: List[str]):
    # Endpoint URL
    url = "http://localhost/api/v1/dataset/"

    # Basic data
    form_data = json.dumps(form_data)

    # Attached files
    files = {}
    for filename in filenames:
        with open(filename, 'rb') as file:
            files[filename] = (filename, file.read())
    files['json'] = ('json', form_data)

    return requests.post(url, files=files)


def uvl_models_populate():

    main_directory = "uvl_models"
    number_of_datasets = 0

    for directory in ["Decision_Models", "Feature_Models", "OVM"]:

        full_directory_path = os.path.join(main_directory, directory)
        visited_paths = []

        for root, dirs, files in os.walk(full_directory_path):

            for dir in dirs:

                dir_path = os.path.join(root, dir)

                # Find recursive
                for subroot, subdirs, subfiles in os.walk(dir_path):

                    # Checks if there are any uvl files in the current directory
                    uvl_files = glob.glob(subroot + "/*.uvl")

                    if uvl_files: # We found a dataset

                        # Since we do recursive scraping, we avoid going through the same directory twice,
                        # to avoid duplicating datasets.
                        if subroot not in visited_paths:

                            visited_paths.append(subroot)
                            number_of_datasets = number_of_datasets + 1

                            # Get basic data
                            main_name = subroot.split("/")[2].replace("_", " ")
                            category_name = subroot.split("/")[3].replace("_", " ") if len(subroot.split("/")) > 3 else ""
                            dataset_name = f"{main_name} ({category_name})" if category_name != "" else f"{main_name}"

                            # print(f"#{number_of_datasets} Dataset name: {dataset_name}, #uvls: {len(uvl_files)}")
                            # print(f"Full path: {subroot}")
                            # print("\n")

                            # Scrapping for each README.md
                            readme_path = os.path.join(subroot, "README.md")
                            publication_doi = ""
                            if os.path.exists(readme_path):
                                try:
                                    with open(readme_path, "r") as readme_file:
                                        first_line = readme_file.readline().strip()

                                    if first_line.startswith("Reference: "):
                                        publication_doi = first_line[len("Reference: "):].replace("-", "")
                                except:
                                    pass

                            # We build basic JSON
                            dataset = {
                                "info": {
                                    "title": dataset_name,
                                    "description": "Unavailable",
                                    "publication_type": "conferencepaper",
                                    "publication_doi": publication_doi,
                                    "tags": [main_name.lower(), category_name.lower(), directory.replace("_", " ").lower()],
                                    "authors": [
                                        {
                                            "name": "Sundermann, Chico",
                                            "affiliation": "Institute of Software Engineering and Programming Languages (Universität ULM",
                                            "orcid": "0000-0002-5239-3307"
                                        },
                                        {
                                            "name": "DiversoLab",
                                            "affiliation": "University of Seville"
                                        }
                                    ]
                                },
                                "models": []
                            }

                            for uvl_file in uvl_files:
                                model = {
                                    "filename": uvl_file
                                }

                                dataset["models"].append(model)

                                # json_data = json.dumps(dataset, indent=4, ensure_ascii=False, sort_keys=True)
                                # print(json_data)

                            # Create dataset in UVLHUB
                            response = create_dataset_endpoint(form_data=dataset, filenames=uvl_files)
                            print(response.text)
                            # time.sleep(1)

    print(f"Number of datasets found: {number_of_datasets}")

uvl_models_populate()

'''

data = {
    "info": {
        "title": "Uplading dataset from UVLHUB REST API",
        "description": "oh yes!",
        "publication_type": "book",
        "publication_doi": "http://",
        "tags": ["tag1", "tag2"],
        "authors": [
            {
                "name": "david romero",
                "affiliation": "University of Seville"
            },
            {
                "name": "pepe benavides",
                "affiliation": "University of Malaga"
            }
        ]
    },
    "models": [
        {
            "filename": "filename1.uvl",
            "title": "hello model 1",
            "description": "hello world",
            "publication_type": "book",
            "publication_doi": "http://",
            "tags": ["tag1", "tag2"],
            "authors": [
                {
                    "name": "david romero",
                    "affiliation": "University of Seville"
                },
                {
                    "name": "pepe benavides",
                    "affiliation": "University of Malaga"
                }
            ]
        },
        {
            "filename": "filename2.uvl",
            "title": "hello model 2",
            "description": "hello world",
            "publication_type": "book",
            "publication_doi": "http://",
            "tags": ["tag1", "tag2"],
            "authors": [
                {
                    "name": "david romero",
                    "affiliation": "University of Seville"
                },
                {
                    "name": "pepe benavides",
                    "affiliation": "University of Malaga"
                }
            ]
        }
    ]
}

filenames = ['filename1.uvl', 'filename2.uvl']

response = create_dataset_endpoint(data, filenames)
print(response.text)

'''
