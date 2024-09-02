import json

class ConfigLoader:
    @staticmethod
    def load_config(file_path):
        with open(file_path, 'r') as config_file:
            return json.load(config_file)

    @staticmethod
    def get(config, key, default=None):
        return config.get(key, default