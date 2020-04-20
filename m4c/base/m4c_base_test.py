import pytest

from .m4c_base import M4CBase

@pytest.fixture
def base():
    return M4CBase()

@pytest.fixture
def random_string():
    import random  
    return ''.join(random.choice('abcdefghijklmn') for x in range(10))  

def test_tables(base):
    base.tables

def test_get_modified_since(base,random_string):
    base.users.update('recKDClFRMdXU0K98', {'Messages (WIP)': random_string})
    base.users.update('recXdffGajY8WYrob', {'Messages (WIP)': random_string})

    from datetime import datetime, timezone, timedelta    
    earlier  = datetime.utcnow() - timedelta(minutes=1)
    earlier = earlier.replace(tzinfo=timezone.utc)
    ret = base.users.get_modified_since(earlier)

    assert len(ret) == 2

def test_get_columns(base):    
    assert base.users.columns['First Name']

def test_rename_readonly_fields(base):
    record = base.users.get('recKDClFRMdXU0K98')
    base.users.rename_readonly_fields(record)


