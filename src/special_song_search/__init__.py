def _import_musicb():
    from . import musicb
    return musicb

def _import_models():
    from . import models
    return models

def _import_database():
    from . import database
    return database

def _import_recommend():
    from . import recommend
    return recommend

musicb = _import_musicb()
models = _import_models()
database = _import_database()
recommend = _import_recommend()
