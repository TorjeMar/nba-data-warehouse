import pandas as pd
from src.utils import disk

if __name__ == '__main__':
    from _v2.utils.provenance import build_provenance_envelope

    input_file = '_data/000_raw/nba/drafthistory/data/drafthistory.json'
    output_file = '_data/000_raw/nba/drafthistory/normalized/drafthistory.json'

    if disk.isfile(output_file):
        print(f'Output file {output_file} already exists, skipping normalization.')
        exit()

    directory, filename = disk.os.path.split(output_file)
    if not disk.isdir(directory):
        disk.makedirs(directory, exist_ok=True)

    data = disk.read_json(input_file)

    data = data['data']['body']['data']['resultSets'][0]

    df = pd.DataFrame(data['rowSet'], columns=data['headers'])
    df = df.astype(object).where(pd.notnull(df), None)

    df.columns = df.columns.str.lower()

    records = df.to_dict(orient='records')

    envelope = build_provenance_envelope(
        data=records,
        source='nba',
        path_input_data=input_file,
        path_processing_script='_data/000_raw/nba/drafthistory/normalize.py',
        is_directory_input=False,
        is_directory_output=False,
    )

    disk.write_json(output_file, envelope)

