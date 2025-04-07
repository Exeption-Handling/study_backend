from fastapi import FastAPI, HTTPException, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "mysql+pymysql://root:sangunhorung-3@localhost/fast_api"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


api = FastAPI()

templates = Jinja2Templates(directory=".")

whether_login = False

# 게시물 데이터 모델
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(String(255), nullable=False)

class User(Base):
    __tablename__ = "users"

    Uindex = Column(Integer, primary_key=True)
    Uid = Column(String(20), nullable=False, unique=True)
    username = Column(String(12), nullable=False, index=True)
    password = Column(String(20), nullable=False)

Base.metadata.create_all(bind=engine)

def get_db(): 
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api.get("/", response_class=HTMLResponse)
def welcome(request:Request):
    global whether_login
    return templates.TemplateResponse("welcome.html", {"request": request, "whether_login":whether_login, "login_success":None, "signup_success":None, "no_permission":None})

@api.get("/sign_up/", response_class=HTMLResponse)
def signing_up(request:Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@api.post("/sign_up/process/", response_class=HTMLResponse)
def process_signing_up(request:Request, Uid:str=Form(...), username:str=Form(...), password:str=Form(...), db:Session=Depends(get_db)):
    new_user = User(Uid=Uid, username=username, password=password)
    scan_user = db.query(User).filter(User.Uid == Uid).first()
    if scan_user is None:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return templates.TemplateResponse("welcome.html", {"request":request, "signup_success":f"{username}님, 성공적으로 회원가입이 완료되었습니다."})
    else: return templates.TemplateResponse("signup.html", {"request":request, "error_message":"이미 존재하는 Uid입니다. 다른 Uid를 입력해주세요!"})

@api.get("/login/", response_class=HTMLResponse)
def log_in(request:Request):
    return templates.TemplateResponse("login.html", {"request":request})

@api.post("/login/process/", response_class=HTMLResponse)
def process_log_in(request:Request, Uid:str=Form(...), password:str=Form(...), db:Session=Depends(get_db)):
    scan_uid = db.query(User).filter(User.Uid==Uid).first()

    if scan_uid is None:
        return templates.TemplateResponse("login.html", {"request":request, "error_message":"존재하지 않는 Uid입니다. 다시 입력해주세요!"})
    else:
        if scan_uid.password != password:
            return templates.TemplateResponse("login.html", {"request":request, "error_message":"비밀번호가 일치하지 않습니다. 다시 입력해주세요!"})
        else:
            global whether_login
            whether_login = True
            return templates.TemplateResponse("welcome.html", {"request":request, "login_success": f"{scan_uid.username}님, 성공적으로 로그인되었습니다.", "whether_login":whether_login})

@api.post("/logout/", response_class=HTMLResponse)
def process_log_out(request:Request):
    global whether_login
    whether_login = False
    return templates.TemplateResponse("welcome.html", {"request":request, "logout_success":"성공적으로 로그아웃되었습니다.", "whether_login":whether_login})

@api.get("/create/", response_class=HTMLResponse)
def creating_post(request:Request):
    global whether_login
    if whether_login == False:
        return templates.TemplateResponse("welcome.html",{"request":request, "whether_login":whether_login, "no_permission":"로그인 후 사용할 수 있는 기능입니다."})
    return templates.TemplateResponse("creatingpost.html", {"request": request})

@api.post("/posts/", response_class=HTMLResponse)
def create_post(request:Request, title:str=Form(...), content:str=Form(...), db: Session = Depends(get_db)):
    
    new_post = Post(title=title, content=content)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return templates.TemplateResponse("post.html", {"request":request, "post":new_post})

@api.post("/posts/{post_id}")
async def DelorMod_post(post_id :int, request:Request, title:Optional[str]=Form(None), content:Optional[str]=Form(None), db:Session=Depends(get_db)):
    form_data = await request.form()
    method = form_data.get("_method","").lower()

    if method == "delete":
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            db.delete(post)
            db.commit()    
            return RedirectResponse("/posts/", status_code=303)
        raise HTTPException(status_code=404, detail="Post not found")
    if method == "modify":
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.title = title or post.title
            post.content = content or post.content
            db.commit()
            db.refresh(post)
            return RedirectResponse("/posts/", status_code=303)
        raise HTTPException(status_code=404, detail="Post not found")
    raise HTTPException(status_code=405, detail="Method not allowed")


@api.get("/modify/{post_id}",response_class=HTMLResponse)
def modifying_post(post_id : int, request:Request, db:Session=Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("modify.html", {"request":request, "post":post})

@api.get("/posts/", response_class=HTMLResponse)
def read_posts(request:Request, db:Session=Depends(get_db)):
    posts = db.query(Post).all()
    return templates.TemplateResponse("posts.html", {"request":request, "posts":posts})

@api.get("/posts/{post_id}", response_class=HTMLResponse)
def read_post(post_id: int, request:Request, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("post.html", {"request":request, "post":post})

