from config import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    is_admin = Column(Boolean, default=False)

class Auction(Base):
    __tablename__ = 'auctions'
    id = Column(Integer, primary_key=True)
    item_desc = Column(Text)
    media_type = Column(String)
    media_file_id = Column(String)
    base_price = Column(Float)
    start_time = Column(DateTime)
    is_active = Column(Boolean, default=True)
    channel_msg_id = Column(Integer, nullable=True)

class Bid(Base):
    __tablename__ = 'bids'
    id = Column(Integer, primary_key=True)
    auction_id = Column(Integer, ForeignKey('auctions.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    time = Column(DateTime, server_default=func.now())

# DB setup
engine = create_async_engine(
    DATABASE_URL, echo=False, future=True
)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
