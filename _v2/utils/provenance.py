from typing import Any
from src.utils import timestamp

def build_provenance_envelope(
    data: Any, 
    path_input_data: str, 
    path_processing_script: str,
    is_directory_output: bool,
    is_directory_input: bool,
    source: str = None,
    **metadata
):
  
    return {
        'timestamp': timestamp(),
        'source': source,
        'is_directory_output': is_directory_output,
        'is_directory_input': is_directory_input,
        'input_data': path_input_data,
        'processing': path_processing_script,
        'metadata': metadata,
        'data': data,
    }
