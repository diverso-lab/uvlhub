import requests
import json

# Endpoint URL
url = "http://localhost/api/v1/dataset/"

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
                "affiliation" : "University of Seville"
            },
            {
                "name": "pepe benavides",
                "affiliation" : "University of Malaga"
            }
        ]
    },
    "models" : [
        {
            "filename" : "filename1.uvl",
            "title": "hello model 1",
            "description": "hello world",
            "publication_type": "book",
            "publication_doi": "http://",
            "tags": ["tag1", "tag2"],
            "authors": [
                {
                    "name": "david romero",
                    "affiliation" : "University of Seville"
                },
                {
                    "name": "pepe benavides",
                    "affiliation" : "University of Malaga"
                }
            ]
        },
        {
            "filename" : "filename2.uvl",
            "title": "hello model 2",
            "description": "hello world",
            "publication_type": "book",
            "publication_doi": "http://",
            "tags": ["tag1", "tag2"],
            "authors": [
                {
                    "name": "david romero",
                    "affiliation" : "University of Seville"
                },
                {
                    "name": "pepe benavides",
                    "affiliation" : "University of Malaga"
                }
            ]
        }
    ]
}

data = json.dumps(data)

filenames = ['filename1.uvl', 'filename2.uvl']

files = {}
for filename in filenames:
    with open(filename, 'rb') as file:
        files[filename] = (filename, file.read())

files['json'] = ('json', data)

response = requests.post(url, files=files)

print(response.text)
