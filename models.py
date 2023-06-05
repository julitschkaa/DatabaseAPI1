from typing import List

import sqlalchemy.sql.sqltypes
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped

from schema import Binary_results

Base  = declarative_base()

class Raw_data(Base):
    __tablename__ = 'raw_data'
    id  = Column(Integer, primary_key=True, index=True)#brauchht's das hier überhaupt wenn Pk=seq_id?
    sequence_id = Column(String)
    sequence = Column(String)
    sequence_length = Column(Integer)#new
    min_quality = Column(Integer)#new
    max_quality = Column(Integer)#new
    average_quality = Column(Float)#new
    phred_quality = Column(String)
    file_id = Column(Integer, ForeignKey('file_name_and_uuid.id'))
    #smart would be to initialise this with an empty list of binary results, but alembic doesnt let me
    file_name_and_uuid = relationship('File_name_and_uuid')

class Binary_results(Base) :
    __tablename__ = 'binary_results'
    id = Column(Integer, primary_key=True, index=True)#same here ist das ding noetig??
    sequence_id = Column(String)
    type = Column(String)
    name = Column(String)
    value = Column(String)
    file_id = Column(Integer, ForeignKey('file_name_and_uuid.id'))

    file_name_and_uuid = relationship('File_name_and_uuid')



class File_name_and_uuid(Base) :
    __tablename__ = 'file_name_and_uuid'
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    file_uuid = Column(String)

