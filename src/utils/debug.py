import json

def prettyprint(data, **kwargs):
    print(json.dumps(data, indent=4, **kwargs))