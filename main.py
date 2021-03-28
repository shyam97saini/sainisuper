from flask import Flask, render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import math
from flask_mail import Mail
from werkzeug.utils import secure_filename

with open('config.json', 'r') as c:
    params = json.loads(c.read())["params"]  
app= Flask(__name__,template_folder='template')
app.secret_key = "super_secret_key"
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = params['email']
app.config['MAIL_PASSWORD'] = params['pwd']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail=Mail(app)
local_server=True
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] =params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] =params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    SRNO = db.Column(db.Integer, primary_key=True)
    NAME = db.Column(db.String(80),nullable=False)
    EMAIL = db.Column(db.String(120),nullable=False)
    PHONE_NUM = db.Column(db.String(120),nullable=False)
    MESSAGE = db.Column(db.String(120),nullable=False)
    DATE = db.Column(db.String(120),nullable=True)
class Posts(db.Model):
    __tablename__ = "posts"
    SNO = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),nullable=False)
    tagline = db.Column(db.String(80),nullable=False)
    slug = db.Column(db.String(25),nullable=False)
    content = db.Column(db.String(120),nullable=False)
    DATE = db.Column(db.String(12),nullable=True)    
    img_file = db.Column(db.String(25),nullable=True)  
@app.route('/')
def home():
    posts=db.session.query(Posts).filter_by().all()
    last = math.ceil(len(posts)/int(params['noOfPost']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int(page)
    posts = posts[(page-1)*int(params['noOfPost']): (page-1)*int(params['noOfPost'])+ int(params['noOfPost'])]
    #Pagination Logic
    #First
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)
@app.route('/dashboard',methods=['GET','POST'])  
def dashboard():
    posts=db.session.query(Posts).all()
    if('user' in session and session['user'] == params['AdminUname']):
        return render_template('dashboard.html',params=params,posts=posts)
    if request.method =='POST':
        username = request.form.get('uname')
        password = request.form.get('pass') 
        print(username,password)
        if username == params['AdminUname'] and password == params['AdminPass']:
            session['user'] = username
            return render_template('dashboard.html',params=params,posts=posts)
        else:
            return redirect('/dashboard')    
    else:
        return render_template('login.html',params=params)  

@app.route('/about')   
def about():
    return render_template('about.html',params=params) 
@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')    

@app.route('/contact',methods=['GET','POST'])
def contact():
    if request.method =='POST':
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        entry=Contacts(NAME=name,EMAIL=email,PHONE_NUM=phone,MESSAGE=message,DATE=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New mesage from '   + name,
        sender = email,
        recipients = [params['email']],
        body = message + "\n" + phone + "\n" + email               
         )
    return render_template('contact.html',params=params)    
@app.route("/post/<slug>",methods=['GET','POST'])   
def post_route(slug):
    post =db.session.query(Posts).filter_by(slug=slug).first()
    return render_template('post.html',params=params,post = post) 

@app.route("/uploader",methods=['GET','POST']) 
def uploader():
    if('user' in session and session['user'] == params['AdminUname']):
        if request.method == 'POST':
            f=request.files['file1']
            base_path = os.path.abspath(os.path.dirname(__file__))
            upload_path = os.path.join(base_path, app.config['UPLOAD_FOLDER'])
            f.save(os.path.join(upload_path, secure_filename(f.filename)))
            return redirect('/dashboard')
@app.route("/delete/<string:SNO>",methods=['GET','POST'])
def delete(SNO):
    if('user' in session and session['user'] == params['AdminUname']):
            post = db.session.query(Posts).filter_by(SNO=SNO).first()
            db.session.delete(post)
            db.session.commit()
    return redirect('/dashboard')    

@app.route("/edit/<string:SNO>",methods=['GET','POST'])  
def edit(SNO):
    print(SNO)
    if('user' in session and session['user'] == params['AdminUname']):
        if request.method == 'POST':
            title=request.form.get('title')
            tagline=request.form.get('tline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            date=datetime.now()
            if SNO =='0':
                post = Posts(title=title,tagline=tagline,slug=slug,content=content,img_file=img_file,DATE=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = db.session.query(Posts).filter_by(SNO=SNO).first()
                post.title = title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.DATE = date
                db.session.commit()
                return redirect('/edit/' + SNO)
        post=db.session.query(Posts).filter_by(SNO=SNO).first()       
        return render_template('edit.html',params=params,post=post,SNO=SNO)         
if __name__=="__main__":
    app.run(debug=True)    
