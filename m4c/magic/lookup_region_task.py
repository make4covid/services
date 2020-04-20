from ..base.m4c_base import M4CBase

base = M4CBase()

def _build_region_lookup():
    import diskcache as dc
    base = M4CBase()
    records = base.regions.get_all()
    record = records[0]
    cache = dc.Cache('regions')
    for record in records:
        key = record['fields']['City'].lower()
        record_id = record['id']
        cache.set(key, record_id)

def _lookup_region(city):
    import diskcache as dc
    cache = dc.Cache('regions')
    return cache.get(city)

normalize_city_name = lambda x : x.lower().strip()

class LookupRegionTask:

    def init(self):
        _build_region_lookup()

    def run(self):
        records = base.maker_production.get_all(max_records = 10, view = 'City -> Region')
        for record in records:
            city = record['fields'].get('City',[''])[0]
            city = normalize_city_name(city)
            region_id = _lookup_region(city)
            print(f'{city}->{region_id}')
            if region_id:
                base.maker_production.update(record['id'], { 'Region': [region_id]})