from sqlalchemy import Column, ForeignKey, Integer, String, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BinaryResult(Base):
    __tablename__ = 'binary_results'
    id = Column(Integer, primary_key=True, index=True)  # same here ist das ding noetig??
    sequence_id = Column(String)
    file_id = Column(Integer, ForeignKey('file_name_and_uuid.id', onupdate='CASCADE', ondelete='CASCADE'))
    name = Column(String)
    type = Column(String)
    value = Column(String)

    file_name_and_uuid = relationship('FileNameAndUuid')


sequence_id_index = Index('sequence_id_index', BinaryResult.sequence_id, postgresql_using='hash')


class FileNameAndUuid(Base):
    __tablename__ = 'file_name_and_uuid'
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, unique=True)
    binary_of_origin = Column(String)
    file_uuid = Column(String)
