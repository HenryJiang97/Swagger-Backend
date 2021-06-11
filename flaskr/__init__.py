import psycopg2
from psycopg2.extras import Json
from flask import Flask
from flask_cors import CORS
from flask import request
from flask import abort
from openapi_spec_validator import validate_v2_spec
from openapi_spec_validator import validate_v3_spec
from flaskr.config.config import POSTGRESQL_URI, TABLENAME
from flaskr.model.Api import Api
from flaskr.service.parser import Parser


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # configure postgres
    connection = psycopg2.connect(POSTGRESQL_URI)
    try:
        create_table(connection)
    except psycopg2.errors.DuplicateTable:
        pass

    # CORS control
    CORS(app)

    # APIs
    # Upload API
    @app.route('/upload', methods=['POST'])
    def upload():
        body = request.get_json()
        # print(body)

        name = body['name']
        title = body['title']
        version = body['version']
        file = Json(body['file'])

        try:
            # Save to db
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"INSERT INTO {TABLENAME} VALUES (%s, %s, %s, %s);", (name, title, version, file))

        except Exception as e:
            # print(e)
            abort(400, 'Error')

        return {"response": "Success"}

    # Download specific API file
    @app.route('/download/<fileName>', methods=['GET'])
    def download(fileName):
        with connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT file FROM {TABLENAME} WHERE name='{fileName}';")
                    files = cursor.fetchall()
                    print(files)
            except FileNotFoundError as e:
                abort(400, 'Error')
        return {"file": files}

    # List file names
    @app.route('/list', methods=['GET'])
    def list():
        with connection:
            try:
                with connection.cursor() as cursor:
                    result = []
                    cursor.execute(f"SELECT name, title, version FROM {TABLENAME};")
                    response = cursor.fetchall()
                    for row in response:
                        print(row)
                        result.append({
                            "name": row[0],
                            "title": row[1],
                            "apiVersion": row[2]
                        })
            except ConnectionError as e:
                abort(400, 'Error')
        # print(result)
        return {"response": result}

    # Clear the table
    @app.route('/clear', methods=['DELETE'])
    def clear():
        try:
            clear_table(connection)
            return {"response": "Success"}
        except ConnectionError as e:
            abort(400, 'Error')

    # Validate API
    @app.route('/validate', methods=['POST'])
    def validate():
        body = request.get_json()
        print(body)
        api_version = body['swagger'] if "swagger" in body else body['openapi']

        try:
            # File validation
            if '2.0' <= api_version < '3.0':
                validate_v2_spec(body)
            else:
                validate_v3_spec(body)

            return {"response": True}
        except:
            return {"response": False}

    # Parse an API file
    @app.route('/parse', methods=['POST'])
    def parse():
        try:
            body = request.get_json()
            parser = Parser(swagger_dict=body)

            # Info
            parser.build_info()

            # Path
            parser.get_paths_data()

            # Definition
            parser.build_definitions_example()

            # print(parser.specification)

        except:
            abort(400, 'File is invalid')

        return {"response": {
            'info': parser.info,
            'base_path': parser.base_path,
            'paths': parser.paths,
            'definitions': parser.definitions_example,
        }}

    return app


def create_table(connection):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE TABLE {TABLENAME} (name TEXT UNIQUE, title TEXT, version TEXT, file JSON);")


def clear_table(connection):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE {TABLENAME};")
            cursor.execute(f"CREATE TABLE {TABLENAME} (name TEXT UNIQUE, title TEXT, version TEXT, file JSON);")
