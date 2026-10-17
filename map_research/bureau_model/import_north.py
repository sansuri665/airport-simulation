"""Read only the reviewed North JSON from a supplied ZIP; never execute it.

py -3 -m bureau_model.import_north path/to/package.zip --scale 0.9
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from .operations import validate_profiles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--scale', type=float, default=.9)
    args = parser.parse_args()
    with zipfile.ZipFile(args.archive) as archive:
        matches = [n for n in archive.namelist() if n.endswith('/huabei10_profiles_v02.json')]
        if len(matches) != 1:
            raise ValueError('Expected one reviewed North profile JSON')
        data = json.loads(archive.read(matches[0]))
    data.update({'schema': 'north10-settlement-v0.1', 'source_archive_sha256': hashlib.sha256(args.archive.read_bytes()).hexdigest(),
                 'status': 'integrated_research_configuration', 'settlement_scale': args.scale})
    for profile in data['bureau_profiles']:
        profile['hidden_freight']['settlement_scale'] = args.scale
        profile.pop('opening_dates_pending_validation', None)
    validate_profiles(data['bureau_profiles'])
    if len(data['bureau_profiles']) != 10 or {p['region_id'] for p in data['bureau_profiles']} != {'north'}:
        raise ValueError('Expected ten North profiles')
    out = Path(__file__).with_name('north10_profiles.json')
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Imported ten North profiles; net settlement scale={args.scale}')


if __name__ == '__main__':
    main()
