from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import bcrypt
import jwt
import os
import logging

from database import engine, get_db, Base
from models import User, MasterUser, Expense, Income, Debt, CreditCard, Gamification, AuditLog
from fastapi.staticfiles import StaticFiles

# Create tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables created successfully")
except Exception as e:
    logging.error(f"Error creating database tables: {e}")
    logging.info("Tables may already exist - continuing...")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'seu-secret-jwt-mude-em-producao-123456789')
JWT_ALGORITHM = 'HS256'

# Create the main app
app = FastAPI(title="Financial Control API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
security = HTTPBearer()

# Pydantic Models
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    cpf: Optional[str] = None
    address: Optional[str] = None
    family_id: Optional[str] = None
    monthly_income: Optional[float] = None
    income_date: Optional[int] = None
    notes: Optional[str] = None

class UserProfile(BaseModel):
    full_name: str
    cpf: Optional[str] = None
    address: Optional[str] = None
    family_id: Optional[str] = None
    monthly_income: Optional[float] = None
    income_date: Optional[int] = None
    notes: Optional[str] = None

class ExpenseCreate(BaseModel):
    category: str
    location: Optional[str] = None
    date: str
    amount: float
    notes: Optional[str] = None
    is_recurring: bool = False
    recurrence_months: Optional[int] = None

class IncomeCreate(BaseModel):
    income_type: str
    amount: float
    date: str
    notes: Optional[str] = None

class DebtCreate(BaseModel):
    description: str
    total_amount: float
    installments: int
    interest_rate: Optional[float] = 0
    status: str = "open"

class CreditCardCreate(BaseModel):
    card_name: str
    closing_date: int
    due_date: int

class MasterLogin(BaseModel):
    username: str
    password: str

class AdminUserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"

# Initialize master user
def init_master_user(db: Session):
    master_username = os.environ.get('MASTER_USERNAME')
    master_password = os.environ.get('MASTER_PASSWORD')
    
    if not master_username or not master_password:
        logging.warning("MASTER_USERNAME or MASTER_PASSWORD not set - skipping master user creation")
        return
    
    master_exists = db.query(MasterUser).filter(MasterUser.username == master_username).first()
    if not master_exists:
        hashed_password = bcrypt.hashpw(master_password.encode('utf-8'), bcrypt.gensalt())
        master = MasterUser(
            username=master_username,
            password_hash=hashed_password.decode('utf-8'),
            role="master"
        )
        db.add(master)
        db.commit()
        logging.info(f"Master user '{master_username}' created")

# @app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        pass # init_master_user(db)
    finally:
        db.close()

# Authentication functions
def create_token(user_id: int, username: str, user_type: str):
    payload = {
        "user_id": str(user_id),
        "username": username,
        "user_type": user_type,
        "exp": datetime.utcnow().timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Routes
@app.get("/")
def root():
    return {"message": "Financial Control API"}

@app.get("/api/")
def api_root():
    return {"message": "Financial Control API"}

# Primary Login
@app.post("/api/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_login.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(user_login.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.id, user.username, 'primary')
    return {
        "token": token,
        "user_id": str(user.id),
        "username": user.username,
        "has_profile": user.full_name is not None
    }

# Master/Admin Login
@app.post("/api/master-login")
def master_login(master_login: MasterLogin, db: Session = Depends(get_db)):
    master = db.query(MasterUser).filter(MasterUser.username == master_login.username).first()
    if not master:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(master_login.password.encode('utf-8'), master.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(master.id, master.username, master.role)
    return {
        "token": token,
        "user_id": str(master.id),
        "username": master.username,
        "role": master.role
    }

# Profile Management
@app.post("/api/profile")
def update_profile(profile: UserProfile, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Only primary users can update profile")
    
    user = db.query(User).filter(User.id == int(payload['user_id'])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.full_name = profile.full_name
    user.cpf = profile.cpf
    user.address = profile.address
    user.family_id = profile.family_id
    user.monthly_income = profile.monthly_income
    user.income_date = profile.income_date
    user.notes = profile.notes
    
    db.commit()
    return {"message": "Profile updated successfully"}

@app.get("/api/profile")
def get_profile(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Only primary users can view profile")
    
    user = db.query(User).filter(User.id == int(payload['user_id'])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "cpf": user.cpf,
        "address": user.address,
        "family_id": user.family_id,
        "monthly_income": user.monthly_income,
        "income_date": user.income_date,
        "notes": user.notes
    }

# Admin - User Management
@app.post("/api/admin/users")
def create_user(user: UserCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] not in ['master', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(
        username=user.username,
        password_hash=hashed_password.decode('utf-8'),
        full_name=user.full_name,
        cpf=user.cpf,
        address=user.address,
        family_id=user.family_id,
        monthly_income=user.monthly_income,
        income_date=user.income_date,
        notes=user.notes
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log action
    audit = AuditLog(
        user_id=int(payload['user_id']),
        action="create_user",
        item_type="user",
        item_id=str(new_user.id),
        details=f"Created user: {user.username}"
    )
    db.add(audit)
    db.commit()
    
    return {"message": "User created successfully", "user_id": str(new_user.id)}

@app.get("/api/admin/users")
def list_users(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] not in ['master', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    users = db.query(User).all()
    return [{
        "id": user.id,
        "_id": str(user.id),
        "username": user.username,
        "full_name": user.full_name,
        "cpf": user.cpf,
        "address": user.address,
        "family_id": user.family_id
    } for user in users]

@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] not in ['master', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    # Log action
    audit = AuditLog(
        user_id=int(payload['user_id']),
        action="delete_user",
        item_type="user",
        item_id=str(user_id),
        details=f"Deleted user: {user_id}"
    )
    db.add(audit)
    db.commit()
    
    return {"message": "User deleted successfully"}

@app.post("/api/admin/create-admin")
def create_admin(admin: AdminUserCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'master':
        raise HTTPException(status_code=403, detail="Only master can create admins")
    
    existing = db.query(MasterUser).filter(MasterUser.username == admin.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = bcrypt.hashpw(admin.password.encode('utf-8'), bcrypt.gensalt())
    new_admin = MasterUser(
        username=admin.username,
        password_hash=hashed_password.decode('utf-8'),
        role="admin"
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return {"message": "Admin created successfully", "admin_id": str(new_admin.id)}

# Expenses
@app.post("/api/expenses")
def create_expense(expense: ExpenseCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    new_expense = Expense(
        user_id=int(payload['user_id']),
        category=expense.category,
        location=expense.location,
        date=expense.date,
        amount=expense.amount,
        notes=expense.notes,
        is_recurring=expense.is_recurring,
        recurrence_months=expense.recurrence_months
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    # If recurring, create additional entries
    if expense.is_recurring and expense.recurrence_months:
        from dateutil.relativedelta import relativedelta
        base_date = datetime.fromisoformat(expense.date)
        
        for i in range(1, expense.recurrence_months):
            next_date = base_date + relativedelta(months=i)
            recurring_expense = Expense(
                user_id=int(payload['user_id']),
                category=expense.category,
                location=expense.location,
                date=next_date.strftime('%Y-%m-%d'),
                amount=expense.amount,
                notes=expense.notes,
                is_recurring=expense.is_recurring,
                parent_expense_id=new_expense.id
            )
            db.add(recurring_expense)
        
        db.commit()
    
    # Log action
    audit = AuditLog(
        user_id=int(payload['user_id']),
        action="add_expense",
        item_type="expense",
        item_id=str(new_expense.id),
        details=f"Added expense: {expense.category} - R$ {expense.amount}"
    )
    db.add(audit)
    db.commit()
    
    # Update gamification
    update_gamification(int(payload['user_id']), db)
    
    return {"message": "Expense created successfully", "expense_id": str(new_expense.id)}

@app.get("/api/expenses")
def get_expenses(month: Optional[str] = None, year: Optional[int] = None, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    query = db.query(Expense).filter(Expense.user_id == int(payload['user_id']))
    
    if month and year:
        month_int = int(month) if isinstance(month, str) else month
        start_date = f"{year}-{month_int:02d}-01"
        if month_int == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month_int + 1:02d}-01"
        query = query.filter(Expense.date >= start_date, Expense.date < end_date)
    
    expenses = query.order_by(Expense.date.desc()).all()
    return [{
        "id": exp.id,
        "_id": str(exp.id),
        "category": exp.category,
        "location": exp.location,
        "date": exp.date,
        "amount": exp.amount,
        "notes": exp.notes,
        "is_recurring": exp.is_recurring,
        "recurrence_months": exp.recurrence_months
    } for exp in expenses]

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == int(payload['user_id'])).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    
    # Log action
    audit = AuditLog(
        user_id=int(payload['user_id']),
        action="delete_expense",
        item_type="expense",
        item_id=str(expense_id),
        details=f"Deleted expense: {expense_id}"
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Expense deleted successfully"}

# Income
@app.post("/api/income")
def create_income(income: IncomeCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    new_income = Income(
        user_id=int(payload['user_id']),
        income_type=income.income_type,
        amount=income.amount,
        date=income.date,
        notes=income.notes
    )
    
    db.add(new_income)
    db.commit()
    
    return {"message": "Income created successfully", "income_id": str(new_income.id)}

@app.get("/api/income")
def get_income(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    incomes = db.query(Income).filter(Income.user_id == int(payload['user_id'])).all()
    return [{
        "id": inc.id,
        "_id": str(inc.id),
        "income_type": inc.income_type,
        "amount": inc.amount,
        "date": inc.date,
        "notes": inc.notes
    } for inc in incomes]

# Debts
@app.post("/api/debts")
def create_debt(debt: DebtCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    new_debt = Debt(
        user_id=int(payload['user_id']),
        description=debt.description,
        total_amount=debt.total_amount,
        installments=debt.installments,
        interest_rate=debt.interest_rate,
        status=debt.status
    )
    
    db.add(new_debt)
    db.commit()
    
    return {"message": "Debt created successfully", "debt_id": str(new_debt.id)}

@app.get("/api/debts")
def get_debts(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    debts = db.query(Debt).filter(Debt.user_id == int(payload['user_id'])).all()
    return [{
        "id": debt.id,
        "_id": str(debt.id),
        "description": debt.description,
        "total_amount": debt.total_amount,
        "installments": debt.installments,
        "interest_rate": debt.interest_rate,
        "status": debt.status
    } for debt in debts]

# Credit Cards
@app.post("/api/credit-cards")
def create_credit_card(card: CreditCardCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    new_card = CreditCard(
        user_id=int(payload['user_id']),
        card_name=card.card_name,
        closing_date=card.closing_date,
        due_date=card.due_date
    )
    
    db.add(new_card)
    db.commit()
    
    return {"message": "Credit card created successfully", "card_id": str(new_card.id)}

@app.get("/api/credit-cards")
def get_credit_cards(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    cards = db.query(CreditCard).filter(CreditCard.user_id == int(payload['user_id'])).all()
    return [{
        "id": card.id,
        "_id": str(card.id),
        "card_name": card.card_name,
        "closing_date": card.closing_date,
        "due_date": card.due_date
    } for card in cards]

# Audit Log
@app.get("/api/audit-log")
def get_audit_log(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] not in ['master', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return [{
        "id": log.id,
        "_id": str(log.id),
        "user_id": log.user_id,
        "action": log.action,
        "item_type": log.item_type,
        "item_id": log.item_id,
        "details": log.details,
        "timestamp": log.timestamp.isoformat()
    } for log in logs]

@app.delete("/api/audit-log/{log_id}")
def delete_audit_log(log_id: int, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] not in ['master', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    db.delete(log)
    db.commit()
    
    return {"message": "Log deleted successfully"}

# Gamification
def update_gamification(user_id: int, db: Session):
    today = date.today()
    gamification = db.query(Gamification).filter(Gamification.user_id == user_id).first()
    
    if not gamification:
        new_gamification = Gamification(
            user_id=user_id,
            points=1,
            streak_days=1,
            last_entry_date=today.isoformat()
        )
        db.add(new_gamification)
    else:
        last_date = datetime.fromisoformat(gamification.last_entry_date).date()
        points = gamification.points + 1
        streak = gamification.streak_days
        
        # Check if entry is on consecutive day
        if (today - last_date).days == 1:
            streak += 1
            points += 5  # Bonus for streak
        elif (today - last_date).days > 1:
            streak = 1  # Reset streak
        
        gamification.points = points
        gamification.streak_days = streak
        gamification.last_entry_date = today.isoformat()
    
    db.commit()

@app.get("/api/gamification")
def get_gamification(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    gamification = db.query(Gamification).filter(Gamification.user_id == int(payload['user_id'])).first()
    if not gamification:
        return {"points": 0, "streak_days": 0}
    
    return {
        "points": gamification.points,
        "streak_days": gamification.streak_days
    }

# Statistics
@app.get("/api/statistics")
def get_statistics(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    if payload['user_type'] != 'primary':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Get total expenses by category
    expenses_by_category = db.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == int(payload['user_id'])
    ).group_by(Expense.category).all()
    
    # Get total income
    user = db.query(User).filter(User.id == int(payload['user_id'])).first()
    total_income = user.monthly_income if user and user.monthly_income else 0
    
    return {
        "expenses_by_category": [{"category": cat, "_id": cat, "total": total} for cat, total in expenses_by_category],
        "total_income": total_income
    }

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Serve frontend HTML
@app.get("/")
async def serve_frontend():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")
