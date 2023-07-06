from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class RawData(Base):
    __tablename__ = 'raw_data'
    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(String, unique=True)  # make sure every read is only present once in
    sequence = Column(String)
    sequence_length = Column(Integer)  # new
    min_quality = Column(Integer)  # new
    max_quality = Column(Integer)  # new
    average_quality = Column(Float)  # new
    phred_quality = Column(String)
    file_id = Column(Integer, ForeignKey('file_name_and_uuid.id'))

    file_name_and_uuid = relationship('FileNameAndUuid')
    binary_results = relationship('BinaryResult', back_populates='raw_data')


class BinaryResult(Base):
    __tablename__ = 'binary_results'
    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(String)
    type = Column(String)
    name = Column(String)
    value = Column(String)
    file_id = Column(Integer, ForeignKey('file_name_and_uuid.id'))
    raw_data_id = Column(Integer, ForeignKey('raw_data.id'))

    file_name_and_uuid = relationship('FileNameAndUuid')
    raw_data = relationship('RawData', back_populates='binary_results')


class FileNameAndUuid(Base):
    __tablename__ = 'file_name_and_uuid'
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    file_uuid = Column(String)
