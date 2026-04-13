from src.utils import disk
from collections import defaultdict

ID_TABLE = dict[str, dict[str, dict[str, str]]]

class IDMapper:
    def __init__(self):
        self.path = '_data/__IDS__.json'
        self.ids: ID_TABLE = defaultdict(lambda : defaultdict(dict))
    
    def __call__(self, namespace: str, key: str, provider: str, provider_id: str, custom_id: str) -> str:
        self.ids[namespace][key].setdefault(provider, provider_id)
        self.ids[namespace][key].setdefault('custom', custom_id)
        
        return self.ids[namespace][key]['custom']
    
    def to_disk(self):
        disk.write_json(self.path, self.ids)
    
    def from_disk(self):
        if disk.isfile(self.path):
            ids: ID_TABLE = disk.read_json(self.path)
            
            for namespace, keys in ids.items():
                for key, providers in keys.items():
                    for provider, provider_id in providers.items():
                        self.ids[namespace][key][provider] = provider_id
        



id_mapper = IDMapper()

