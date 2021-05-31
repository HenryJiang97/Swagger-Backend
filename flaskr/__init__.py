import psycopg2
import psycopg2.extras
import json

from flask import Flask
from flask_cors import CORS
from flask import request
import swagger_parser
from yaml import load;
from openapi_spec_validator import validate_v2_spec
from openapi_spec_validator import validate_v3_spec
from swagger_parser import SwaggerParser


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config["ALLOWED_EXTENSIONS"] = [".yaml"]
    

    # configure postgres
    POSTGRESQL_URI = 'postgresql://postgres:123456@localhost:5432/swagger_api'
    connection = psycopg2.connect(POSTGRESQL_URI)
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE TABLE files (name TEXT UNIQUE, file JSON);")
    except psycopg2.errors.DuplicateTable:
        pass

    CORS(app)


    # APIs

    # Upload API
    @app.route('/upload/<version>', methods=['POST'])
    def upload(version):
        file = request.files['file']
        print(file)
        if (file):
            try:
                # Get file json
                print(f'file: {file.filename}')
                filename = file.filename
                file_obj = load(file)
                file_json = json.dumps(file_obj)

                # File validation
                if (version == "2"):
                    validate_v2_spec(file_obj)
                else:
                    validate_v3_spec(file_obj)
                
                # Save to db
                with connection:
                    with connection.cursor() as cursor:
                        cursor.execute("INSERT INTO files VALUES (%s, %s);", (filename, file_json))

            except Exception as e:
                print(e);
                return {"response": "Not valid"}
                
        else:
            print('file: null')

        return {"response": "Success"}


    # Download specific API file
    @app.route('/download/<fileName>', methods=['GET'])
    def download(fileName):
        print(fileName)
        with connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT file FROM files WHERE name='{fileName}';")
                    files = cursor.fetchall()
                    print(files)
            except:
                return {"file": None}
        return {"file": files}


    # List file names
    @app.route('/list', methods=['GET'])
    def list():
        with connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT name FROM files;")
                    names = cursor.fetchall()
            except:
                return {"names": []}
        print(names)
        return {"names": names}

    
    # Drop the files table
    @app.route('/drop', methods=['DELETE'])
    def drop():
        with connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DROP TABLE files;")
            except:
                return {"response": "Error"}
        return {"response": "Success"}


    # Get API details
    @app.route('/details', methods=['POST'])
    def details():
        file = request.files['file']
        if (file):
            try:
                file_obj = load(file)
                # print(file_obj)

                parser = SwaggerParser(swagger_dict=file_obj)
                data = parser.get_send_request_correct_body('/estimates/price', 'get')
                print(data)

                return {"response": file_obj}

            except Exception as e:
                print(e);
                return {"response": "Not valid"}

        else:
            print('file: null')
        
        return {"response": "Success"}

    return app