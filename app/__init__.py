# !/user/bin/env python
# -*- coding:utf-8 -*- 



from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os

from sqlalchemy.orm import Query

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@127.0.0.1:33060/news_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UP_DIR'] = os.path.join(os.path.abspath(os.path.dirname(__file__)),'static/uploads/') #定义后台上传的文件的保存路径
app.config['FC_DIR'] = os.path.join(os.path.abspath(os.path.dirname(__file__)),'static/uploads/users/') #定义前台上传的用户头像文件的保存路径

app.debug = False #开发调试模式

# app.config['SECRET_KEY'] = 'Henry'
app.secret_key = '子龙' #密钥:用于csrf加密 Henry

db = SQLAlchemy(app)

from app.home import home as home_blueprint

app.register_blueprint(home_blueprint)


# 404页面
@app.errorhandler(404)
def page_not_found(error):
    return render_template('home/404.html'), 404
