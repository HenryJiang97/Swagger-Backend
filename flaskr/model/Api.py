class Api:
    def __init__(self, name, title, version, description, host, paths, definitions):
        self.name = name
        self.title = title
        self.version = version
        self.description = description
        self.host = host
        self.paths = paths
        self.definitions = definitions

