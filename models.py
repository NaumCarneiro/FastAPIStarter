from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    cpf = Column(String(14))
    address = Column(Text)
    family_id = Column(String(100))
    monthly_income = Column(Float)
    income_date = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    debts = relationship("Debt", back_populates="user", cascade="all, delete-orphan")
    credit_cards = relationship("CreditCard", back_populates="user", cascade="all, delete-orphan")
    gamification = relationship("Gamification", back_populates="user", uselist=False, cascade="all, delete-orphan")

class MasterUser(Base):
    __tablename__ = "master_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")  # master or admin
    created_at = Column(DateTime, default=datetime.utcnow)

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False)
    location = Column(String(200))
    date = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    notes = Column(Text)
    is_recurring = Column(Boolean, default=False)
    recurrence_months = Column(Integer)
    parent_expense_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="expenses")

class Income(Base):
    __tablename__ = "income"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    income_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(String(20), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="incomes")

class Debt(Base):
    __tablename__ = "debts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String(200), nullable=False)
    total_amount = Column(Float, nullable=False)
    installments = Column(Integer, nullable=False)
    interest_rate = Column(Float, default=0)
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="debts")

class CreditCard(Base):
    __tablename__ = "credit_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_name = Column(String(100), nullable=False)
    closing_date = Column(Integer, nullable=False)
    due_date = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="credit_cards")

class Gamification(Base):
    __tablename__ = "gamification"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    points = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_entry_date = Column(String(20))
    
    user = relationship("User", back_populates="gamification")

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    item_type = Column(String(50))
    item_id = Column(String(50))
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
