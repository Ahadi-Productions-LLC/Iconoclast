from dataclasses import fields

def dataclass_from_dict(klass, d):
    try:
        fieldtypes = {f.name:f.type for f in fields(klass)}
        return klass(**{f:dataclass_from_dict(fieldtypes[f],d[f]) for f in d if f in fieldtypes})
    except Exception as e:
        return d # Not a dataclass field