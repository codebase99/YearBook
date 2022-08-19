# from crypt import methods
from flask import Flask, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_cors import CORS

import psycopg2
import uuid
import datetime
import redis


app = Flask(__name__)

app.secret_key = "276duC4d09"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_REDIS"]=redis.from_url("redis://127.0.0.1:6379")
app.config["SESSION_REFRESH_EACH_REQUEST"] = False
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
server_session = Session(app)
CORS(app, supports_credentials=True)

def login_required(func):
        if not "user" in session:
            return {"message": "please login"}

@app.before_request
def before_request_func():
    print(request.path)
    if request.path == "/login" or request.path == "/about" or request.path=="/register":
        print("leaving before request func")
        pass
    else:
        if not session.get("user"):
            print("stuck in before request func")
            return {"message":"you are logged out"}

def get_db_connection():
    conn = psycopg2.connect(
            host="localhost",
            database="YearBook",
            user="postgres",
            password="password")
    return conn




def check_username(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"select login.username from login where login.username = '{username}'")
    res = cur.fetchall()
    cur.close()
    conn.close()
    print(f"received {res}")
    return True if len(res)>0 else False

def check_email(email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"select userinfo.email from userinfo where userinfo.email = '{email}'")
    res = cur.fetchall()
    cur.close()
    conn.close()
    print(f"received {res}")
    return True if len(res)>0 else False

def check_password(username, password):
    print(username, password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"select login.hash from login where login.username = '{username}'")
    res = cur.fetchall()
    cur.close()
    conn.close()
    print(f"res = {res}")
    print(res[0][0], username, password)
    if len(res)== 0:
        return False
    return True if res[0][0]==password else False

def insert_userinfo_to_db(fname,lname,email,username,password):
    print(username)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO userinfo (username,dob,email,fname,lname)VALUES('{username}','2000-12-31', '{email}', '{fname}', '{lname}');")
    cur.execute(f"INSERT INTO login (username,hash)VALUES('{username}','{password}');")
    
    cur.close()
    conn.commit()
    conn.close()
   

def get_user_posts(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"select * from posts where posts.username = '{username}'")
    res = cur.fetchall()
    cur.close()
    conn.close()
    posts = []
    for post in res:
        print(post)
        (postid, pictureid, date, likes, dislikes, shares, username ,caption) = post
        posts.append({"postid":postid,
            "pictureid":pictureid,
            "date": date,
            "likes": likes,
            "dislikes": dislikes,
            "shares": shares,
            "username": username,
            "caption": caption
        })
    print(posts)
    return posts

def get_posts():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"select * from posts")
    res = cur.fetchall()
    cur.close()
    conn.close()
    posts = []
    for post in res:
        print(post)
        (postid, pictureid, date, likes, dislikes, shares, username ,caption) = post
        posts.append({"postid":postid,
            "pictureid":pictureid,
            "date": date,
            "likes": likes,
            "dislikes": dislikes,
            "shares": shares,
            "username": username,
            "caption": caption
        })
    print(posts)
    return posts
    


@app.route("/me" )
def get_me():
    if "user" not in session:
        return {"message":"not logged in"}
    user = str(session["user"])
    return  {"message":user}

@app.route('/')
def home():
    return f"<h1> Hello {session['user']}"

@app.route('/login', methods = ['POST'])
def login():
    print("logged in:")

    print("user" in session)
    if "user" in session:
        return {"message" : "you are logged in"}, 200
    print(request.json)
    username = request.json["username"]
    password = request.json["password"]

    valid_username = check_username(username)
    print(valid_username)
    if not valid_username:
        return {"message":"user not found"}
    valid_password = check_password(username, password)
    print(valid_password)
    if not valid_password:
        return {"message": "invalid username or password"}
    print(f'valid_username = {valid_username}, valid_password = {valid_password}')
    
    session["user"] = username
    print("logged in:")

    print("user" in session)

    return {"message": "success"}, 200
    

@app.route('/logout')
def logout():
    print("hello")
    print('lala')
    session.pop("user", None)
    print("user" in session)
    
    return {"message":"you have logged out"}

 

@app.route('/register', methods = ["POST"])
def register():
    fname = request.json["fname"]
    lname = request.json["lname"]
    # dob = request.json["dob"]
    email = request.json["email"]
    username = request.json["username"]
    password = request.json["password"]

    print(fname , lname, email, username, password)

    if check_username(username):
        return {"message":"Username already exists"}

    if check_email(email):
        return {"message": "email already being used"}

    
    print(fname,lname,email,username,password)
    insert_userinfo_to_db(fname,lname,email,username,password)
    return {"message":"Resgistration sucessful"}, 200

@app.route('/user/<username>')
def get_user_profile(username):
    valid = check_username(username)
    if not valid:
        return {"message":"invalid user"}, 404 
    return jsonify(get_user_posts(username))
    
@app.route('/post', methods = ["POST"])
def post():
    username = session['user']
    postid = uuid.uuid4()
    pictureid = uuid.uuid4()
    date = datetime.date.today().strftime("%Y-%m-%d")
    likes = 0
    dislikes = 0
    shares = 0
    caption = request.files["caption"]
    # file = request.files['post-image']
    # print(file.filename)
    file = request.files['post-image']
    # print(file.filename)
    # image=request.files['post-image']
    # PATH = './Post Images/'
    # print(request.json)
    # return {}
    print(request)
    
    print(username, postid, pictureid, date, likes, shares, dislikes, caption)
    return {"postid":f'{postid}'}

@app.route('/postimage', methods = ["POST"])
def postImage():
    
    caption = request.json["caption"]
    file = request.files['post-image']
    file.save('./Post Images/test_image.jpg')   
    return {}

@app.route('/getPosts')
def getPosts():
    
    print(f"getting posts....")
    posts = get_posts()
    print("the posts are:")
    print(posts)
    return jsonify(posts)





 




