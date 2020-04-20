from airtable import Airtable
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import os

AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
AIRTABLE_M4C_BASE_KEY = os.environ['AIRTABLE_M4C_BASE_KEY']

with open(Path(__file__).parent / 'applahkO2yeDOzBFB.json') as f:
  base_schema = json.load(f)

non_writable_column_types = ['formula', 'lookup', 'multipleAttachment']
    
def parse_airtable_timestamp(date_str):
    do = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.000Z')
    return do.replace(tzinfo=timezone.utc)


tables = [
    ('tbl88dJxsFd7fcTH2', 'Maker Production'),
    ('tblBGSTm13uFTcw5S', 'Users'),
    ('tblV01D6PysZMnjdn', 'Maker Information'),
    ('tblyRQF7ekQsGQauh', 'Key Locations'),    
]

id2name = { id: name for id, name in tables }    
name2id = { name: id for id, name in tables }


class MyAirtable(Airtable):
        
    def __init__(self, base_key, table_id, api_key):
        Airtable.__init__(self, base_key, table_id, api_key)
        self.schema = base_schema[table_id]
        
    @property
    def columns(self):
        columns_array = self.schema['columns']
        columns_dict = { col['name']: col for col in columns_array }
        return columns_dict

    @property
    def writable_columns(self):
        return {k: v for k, v in self.columns.items() if v['type'] not in non_writable_column_types}
    
    def get_writables(self, record_id):
        record = self.get(record_id)
        fields = record['fields']
        cols = self.writable_columns
        # cols_dict = { col['name']: col for col in cols }
        writable_fields = { k : v for k, v in fields.items() if k in cols}
        record['fields'] = writable_fields
        return record

    def update_writables(self, record_id, fields, typecast=False):        
        """
            
            automatically skip those fields that can not be updated (e.g., formula, lookup)
        
        """
        
        cols = self.writable_columns
        cols_dict = { col['name']: col for col in cols }
        writable_fields = { k : v for k, v in fields.items() if k in cols_dict}
                
        Airtable.update(self, record_id, writable_fields, typecast)
        
    def get_modified_since(self, datetime_since):
    
        modified_records = []

        def convert_last_modified_time(record):
            last_modified_time = record['fields']['Last modified time']
            datetime_last_modified = parse_airtable_timestamp(last_modified_time)
            record['fields']['Last modified time'] = datetime_last_modified

        def is_modified_since_last_sync(record):
            last_modified_time = record['fields']['Last modified time']
            # datetime_last_modified = parse_airtable_timestamp(last_modified_time)
            if datetime_since:
                return last_modified_time > datetime_since    
            else:
                return True

        for page in self.get_iter(page_size = 20, sort = [('Last modified time', 'desc')]):
            for record in page:
                convert_last_modified_time(record)
                if not is_modified_since_last_sync(record):
                    return modified_records

                modified_records.append(record)

        return modified_records   
          
    def rename_readonly_fields(self, record):
    
        columns_dict = { col['name']: col for col in self.columns }

        new_record = {
            'id': record['id'],
            'fields': {}
        }
        for k, v in record['fields'].items():
            if columns_dict.get(k) and columns_dict[k]['type'] in non_writable_column_types:
                k1 = '$' + k
            else:
                k1 = k
            new_record['fields'][k1] = v
        return new_record

class M4CBase:

    def __init__(self):
 
        self.maker_information = MyAirtable(AIRTABLE_M4C_BASE_KEY, 'tblV01D6PysZMnjdn', api_key=AIRTABLE_API_KEY)
        self.users = MyAirtable(AIRTABLE_M4C_BASE_KEY, 'tblBGSTm13uFTcw5S', api_key=AIRTABLE_API_KEY)
        self.maker_production = MyAirtable(AIRTABLE_M4C_BASE_KEY, 'tbl88dJxsFd7fcTH2', api_key=AIRTABLE_API_KEY)
        self.maker_supply_requests = MyAirtable(AIRTABLE_M4C_BASE_KEY, 'tblAS9hFkRwkwwHqj', api_key=AIRTABLE_API_KEY)
        self.shipping = MyAirtable(AIRTABLE_M4C_BASE_KEY, 'tblCnJGc2lRohQSMi', api_key=AIRTABLE_API_KEY)
        self.equipment_requests = MyAirtable(AIRTABLE_M4C_BASE_KEY, 'tbl6yaV3QsOjAnoIq', api_key=AIRTABLE_API_KEY)
        self.key_locations = MyAirtable(AIRTABLE_M4C_BASE_KEY, 'tblyRQF7ekQsGQauh', api_key=AIRTABLE_API_KEY)
        self.messages = MyAirtable(AIRTABLE_M4C_BASE_KEY, 'tblxeZ6CrHQgTwRbC', api_key=AIRTABLE_API_KEY)
    
    @property
    def tables(self):
        return {
            'Users': self.users, 
            'Maker Information': self.maker_information,
            'Maker Production': self.maker_production,
            'Maker Supply Requests': self.maker_supply_requests,
            'Equipment Requests':self.equipment_requests,
            'Shipping': self.shipping,
            'Key Locations': self.key_locations,
            'Messages': self.messages
        }     
