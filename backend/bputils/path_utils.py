import os
import sys


def get_project_root():
    try:
        from flask import current_app
        resource_path = current_app.config.get('RESOURCE_PATH')
        if resource_path:
            return resource_path
    except Exception:
        pass
    
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(utils_dir)
    return os.path.dirname(backend_dir)


def get_config_path():
    try:
        from flask import current_app
        config_path = current_app.config.get('CONFIG_PATH')
        if config_path:
            return config_path
    except Exception:
        pass
    
    return os.path.join(get_project_root(), "config.json")


def get_resource_path(relative_path):
    return os.path.join(get_project_root(), relative_path)