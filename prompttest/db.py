from sqlalchemy import Column, Integer, String, DateTime, Float, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import datetime

engine = create_engine("sqlite:///database.db", echo=False)
_SessionFactory = sessionmaker(bind=engine)

Base = declarative_base()

class Runs(Base):
    __tablename__ = 'runs'

    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)
    model = Column(String)
    temperature = Column(Float)
    name = Column(String)
    prompt = Column(String)
    variables = Column(String)
    response = Column(String)
    ranking = Column(Integer)

def session_factory():
    Base.metadata.create_all(engine)
    return _SessionFactory()

def create_db():
    session = session_factory()
    session.close()

def add_row(model: str, temperature: float, name: str, prompt: str, variable_list: list[str], response: str, ranking: int):
    session = Session(bind=engine)
    variables = ','.join(variable_list)

    data = Runs(
            model=model,
            temperature=temperature, 
            name=name,
            prompt=prompt,
            variables=variables,
            response=response,
            ranking=ranking
            )

    session.add(data)
    session.commit()

    session.close()
    return

def delete_rows(list_id: list[int]):
    session = Session(bind=engine)
    session.query(Runs).filter(Runs.id.in_(list_id)).delete()
    session.commit()
    session.close()
    return

def get_row(id: int):
    session = Session(bind=engine)
    row = session.query(Runs).filter(Runs.id == id)[0]
    row_dict = {'run_name': row.name, 'prompt_template': row.prompt} 
    return row_dict

if __name__ == "__main__":
    create_db()
