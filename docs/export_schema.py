import sys
import os

sys.path.insert(0, os.path.abspath('./backend'))

from sqlalchemy import create_mock_engine
from database import Base
import models

def dump_sql(sql, *multiparams, **params):
    with open('schema.sql', 'a', encoding='utf-8') as f:
        f.write(sql.compile(dialect=engine.dialect).string + ';\n')

# Clean output file
open('schema.sql', 'w', encoding='utf-8').close()

engine = create_mock_engine('postgresql://', dump_sql)
Base.metadata.create_all(engine, checkfirst=False)
