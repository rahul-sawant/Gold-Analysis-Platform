from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.config.config import DATABASE_URL
from app.data.models import Base

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CRUDBase:
    """Base class for CRUD operations."""
    
    def __init__(self, model):
        self.model = model
    
    def get(self, db: Session, id: int):
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in):
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj, obj_in):
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: int):
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


# Create CRUD classes for each model
from app.data.models import PriceData, TechnicalIndicator, PricePrediction, Trade

class PriceDataCRUD(CRUDBase):
    def __init__(self):
        super().__init__(PriceData)
    
    def get_by_timeframe(self, db: Session, timeframe: str, limit: int = 100):
        return db.query(self.model).filter(self.model.timeframe == timeframe).order_by(self.model.timestamp.desc()).limit(limit).all()
    
    def get_latest(self, db: Session, source: str, timeframe: str):
        return db.query(self.model).filter(self.model.source == source, self.model.timeframe == timeframe).order_by(self.model.timestamp.desc()).first()


class TechnicalIndicatorCRUD(CRUDBase):
    def __init__(self):
        super().__init__(TechnicalIndicator)
    
    def get_by_price_data(self, db: Session, price_data_id: int):
        return db.query(self.model).filter(self.model.price_data_id == price_data_id).first()


class PricePredictionCRUD(CRUDBase):
    def __init__(self):
        super().__init__(PricePrediction)
    
    def get_latest_prediction(self, db: Session, model_name: str, timeframe: str):
        return db.query(self.model).filter(
            self.model.model_name == model_name,
            self.model.prediction_timeframe == timeframe
        ).order_by(self.model.timestamp.desc()).first()


class TradeCRUD(CRUDBase):
    def __init__(self):
        super().__init__(Trade)
    
    def get_open_trades(self, db: Session):
        return db.query(self.model).filter(self.model.exit_price.is_(None)).all()
    
    def get_trades_by_date_range(self, db: Session, start_date, end_date):
        return db.query(self.model).filter(
            self.model.timestamp >= start_date,
            self.model.timestamp <= end_date
        ).all()


# Initialize CRUD instances
price_data_crud = PriceDataCRUD()
indicator_crud = TechnicalIndicatorCRUD()
prediction_crud = PricePredictionCRUD()
trade_crud = TradeCRUD() 