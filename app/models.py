# !/user/bin/env python
# -*- coding:utf-8 -*- 



from app import db
from datetime import datetime


# 会员模型
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 用户名
    pwd = db.Column(db.String(100))  # 密码
    email = db.Column(db.String(100), unique=True)  # 邮箱
    phone = db.Column(db.String(11), unique=True)  # 手机号
    info = db.Column(db.Text)  # 个性简介
    face = db.Column(db.String(255), unique=True)  # 头像
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 注册时间
    uuid = db.Column(db.String(255), unique=True)  # 唯一标识符

    userlogs = db.relationship('Userlog', backref='user')  # 会员日志外键关系关联
    bookcols = db.relationship('Newscol', backref='user')  # 新闻收藏外键关系关联

    def __repr__(self):
        return '<User %r>' % self.name

    def check_pwd(self,pwd):
        '''加密并验证用户的密码是否正确'''
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd,pwd)


# 会员登录日志
class Userlog(db.Model):
    __tablename__ = 'userlog'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 用户ID
    ip = db.Column(db.String(100))  # 用户IP地址
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 登录时间

    def __repr__(self):
        return '<Userlog %r>' % self.id


# 标签
class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 标签名
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 标签的添加时间

    news = db.relationship('News', backref='tag')  # 新闻外键关系关联

    def __repr__(self):
        return '<Tag %r>' % self.name


# 新闻
class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    logo = db.Column(db.String(2550))  # 新闻封面
    link = db.Column(db.String(2550))  # 新闻链接
    title = db.Column(db.String(2550))  # 新闻名
    info = db.Column(db.Text)  # 新闻内容
    commentnum = db.Column(db.BigInteger)  # 浏览数
    media = db.Column(db.String(2550))  # 新闻类别
    star = db.Column(db.Integer)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))  # 标签ID
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 添加时间

    newscols = db.relationship('Newscol', backref='news')  # 新闻收藏外键关系关联

    def __repr__(self):
        return '<News %r>' % self.title

# 评分
class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    newsid = db.Column(db.Integer)
    rating = db.Column(db.Integer)

    def __repr__(self):
        return '<Rating %r>' % self.id

# 收藏新闻
class Newscol(db.Model):
    __tablename__ = 'newscol'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'))  # 所属新闻
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 所属用户
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 添加时间

    def __repr__(self):
        return '<Newscol %r>' % self.id


# 定义角色的权限
# class Auth(db.Model):
#     __tablename__ = 'auth'
#     id = db.Column(db.Integer, primary_key=True)  # 编号
#     name = db.Column(db.String(100), unique=True)  # 权限名
#     url = db.Column(db.String(255), unique=True)  # 权限url地址
#     addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 创建时间
#
#     def __repr__(self):
#         return '<Auth %r>' % self.name



