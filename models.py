import sqlalchemy.sql.sqltypes
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base  = declarative_base()

class Raw_data(Base):
    __tablename__ = 'raw_data'
    id  = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(String)
    sequence = Column(String)
    phred_quality = Column(String)
    file_id = Column(Integer, ForeignKey('file_name_and_uuid.id'))

    file_name_and_uuid = relationship('File_name_and_uuid')

class Binary_results(Base) :
    __tablename__ = 'binary_results'
    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(String)
    mapping_reference_file = Column(sqlalchemy.sql.sqltypes.String)
    binary_of_origin = Column(String)
    type = Column(String)
    value = Column(Float)


class File_name_and_uuid(Base) :
    __tablename__ = 'file_name_and_uuid'
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    file_uuid = Column(String)

