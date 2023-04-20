# !/user/bin/env python
# -*- coding:utf-8 -*-
from ItemCF import ItemBasedCF
from UserCF import UserBasedCF
from . import home
from flask import render_template, url_for, redirect, flash, session, request
from app.home.forms import RegistForm, LoginForm, UserdetailForm, PwdForm, CommentForm, StarForm
from app.models import User, Userlog, News, Tag, Newscol, Rating
from app import db, app
import uuid  # 添加唯一标志符
from werkzeug.security import generate_password_hash
from functools import wraps  # 装饰器(用于访问控制)
from werkzeug.utils import secure_filename
import os, stat, datetime

import pymysql
import traceback
import json


# 修改上传的文件名称
def change_filename(filename):
    # fileinfo = os.path.splitext(filename)  # 取出上传的文件名的后缀(.MP4)
    fileinfo = filename.split('.')  # 取出上传的文件名的后缀(.MP4)
    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + '.' + fileinfo[-1]
    return filename


# 前台登录装饰器(只能登录后才能访问会员中心)
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:  # if session['user'] is None:
            return redirect(url_for('home.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 首页重定向
@home.route('/', methods=['GET'])
def index_1():
    return redirect('/1/')


# 首页
@home.route('/<int:page>/', methods=['GET'])
def index(page=None):
    # 新闻筛选 (默认按新闻上传时间排,最新上传的在最前面)
    tags = Tag.query.all()
    page_data = News.query.order_by(
        News.id.desc()
    )
    # 1.新闻标签
    tid = request.args.get('tid', 0)

    if int(tid) != 0:
        page_data = page_data.filter_by(tag_id=int(tid))

    # 3.添加时间(最近,最早)
    time = request.args.get('time', 0)
    # if int(time) != 0:
    #     if int(time) == 1: #降序(最近)
    #         page_data = News.query.order_by(
    #             News.addtime.desc()
    #         )
    #     else: #升序(最早) if int(time) == 2
    #         page_data = News.query.order_by(
    #             News.addtime.asc()
    #         )

    if page == None:
        page = 1
    page_data = page_data.paginate(page=page, per_page=12)
    # 将上面接受到的参数组成一个字典p，       下方p可用可不用
    p = dict(
        tid=tid,
        time=time,
    )

    # 获得新闻标签表的对应列
    news_tag = Tag.query.filter_by(id=int(tid)).first()

    page_data.key = tid
    for v in page_data.items:
        if 'user' in session:
            # 获取当前用户对此新闻的评分
            r = Rating.query.filter_by(
                newsid=v.id,
                userid=session['user_id']
            ).first()
            if r:
                v.star = r.rating
                if v.star > 5:
                    v.star = 5
            else:
                v.star = 0
        else:
            if v.star > 5:
                v.star = 5

    return render_template('home/index.html', tags=tags, p=p, news_tag=news_tag, page_data=page_data)


# 登录
@home.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=data['name']).first()

        if not user:
            flash('没有此用户名!', 'err')
            return redirect(url_for('home.login'))
        if user.check_pwd(data['pwd']) == False:  # 验证密码是否正确
            flash('密码错误!', 'err')
            return redirect(url_for('home.login'))
        # 登录成功则保存会话:
        session['user'] = user.name  # 用户名
        session['user_id'] = user.id  # 用户ID
        # 将登录操作存入会员登陆日志
        userlog = Userlog(
            user_id=session['user_id'],
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for('home.user'))  # 登录成功跳到会员中心
    return render_template('home/login.html', form=form)


# 登出
@home.route('/logout/')
def logout():
    # 删除会话
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('home.login'))


# 注册
@home.route('/regist/', methods=['GET', 'POST'])
def regist():
    form = RegistForm()
    if form.validate_on_submit():
        data = form.data
        # 查询用户名是否存在
        name = data['name']
        user = User.query.filter_by(name=name).count()
        if user == 1:
            flash('此昵称已存在!', 'err')
            return render_template('home/regist.html', form=form)

        email = data['email']
        user = User.query.filter_by(email=email).count()
        if user == 1:
            flash('此邮箱已存在!', 'err')
            return render_template('home/regist.html', form=form)

        phone = data['phone']
        user = User.query.filter_by(phone=phone).count()
        if user == 1:
            flash('此手机号已存在!', 'err')
            return render_template('home/regist.html', form=form)

        user = User(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            pwd=generate_password_hash(data['pwd']),  # 加密用户的密码
            uuid=uuid.uuid4().hex  # 生成用户的唯一标志符
        )
        db.session.add(user)
        db.session.commit()
        flash('恭喜您,注册成功!', 'ok')
        return redirect(url_for('home.login'))
    return render_template('home/regist.html', form=form)


# 会员中心(可修改会员资料)
@home.route('/user/', methods=['GET', 'POST'])
@user_login_req  # 只有登录后才能访问会员中心
def user():
    form = UserdetailForm()
    user = User.query.get_or_404(session['user_id'])
    # form.face.validators = []
    # 获取用户现在的会员信息(get)
    if request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    # 修改会员信息(post)
    if form.validate_on_submit():
        data = form.data
        # 如果用户名已经存在,则修改失败
        user_name = User.query.filter_by(name=data['name']).count()
        if user_name == 1 and user.name != data['name']:
            flash('用户昵称已存在,请重新输入!', 'err')
            return redirect(url_for('home.user'))
        # 如果邮箱以存在,则修改失败
        user_email = User.query.filter_by(email=data['email']).count()
        if user_email == 1 and user.email != data['email']:
            flash('邮箱已存在,请重新输入!', 'err')
            return redirect(url_for('home.user'))
        # 如果手机号以存在,则修改失败
        user_phone = User.query.filter_by(phone=data['phone']).count()
        if user_phone == 1 and user.phone != data['phone']:
            flash('手机号已存在,请重新输入!', 'err')
            return redirect(url_for('home.user'))

        # 修改头像
        if not os.path.exists(app.config['FC_DIR']):  # 没有就创建文件夹
            os.makedirs(app.config['FC_DIR'])
            # os.chmod(app.config['FC_DIR'], 'rw')  # 给文件夹可读可写的权限,这样才能保存文件呀
            os.chmod(app.config['FC_DIR'], stat.S_IRWXU)  # 给文件夹可读可写的权限,这样才能保存文件呀 'rw'
        # 如果face不为空,即为修改了头像地址,要重新保存
        # 上传头像文件,一定要加上enctype="multipart/form-data"
        # print(form.face.data.filename)
        if form.face.data.filename != '':
            file_face = secure_filename(form.face.data.filename)  # 生成上传的新闻封面的文件名,并安全加密
            # print(file_face)
            user.face = change_filename(file_face)
            form.face.data.save(app.config['FC_DIR'] + user.face)
        # 修改入库
        user.name = data['name'],
        user.email = data['email'],
        user.phone = data['phone'],
        user.info = data['info'],
        db.session.add(user)
        db.session.commit()
        flash('修改资料成功!', 'ok')
        return redirect(url_for('home.user'))
    return render_template('home/user.html', form=form, user=user)


# 1.修改密码
@home.route('/pwd/', methods=['GET', 'POST'])
@user_login_req
def pwd():
    form = PwdForm()
    user = User.query.filter_by(id=session['user_id']).first()
    if form.validate_on_submit():
        data = form.data
        if not user.check_pwd(data['old_pwd']):
            flash('旧密码错误!请重新输入!', 'err')
            return redirect(url_for('home.pwd'))
        user.pwd = generate_password_hash(data['new_pwd'])
        db.session.add(user)
        db.session.commit()
        flash('修改密码成功!', 'ok')
        return redirect(url_for('home.logout'))
    return render_template('home/pwd.html', form=form)


# 3.登录日志
@home.route('/loginlog/<int:page>/', methods=['GET'])
@user_login_req
def loginlog(page=None):
    if page == None:
        page = 1
    page_data = Userlog.query.filter_by(
        user_id=session['user_id']
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('home/loginlog.html', page_data=page_data)


# 4.新闻收藏
@home.route('/newscol/<int:page>/', methods=['GET'])
@user_login_req
def newscol(page=None):
    if page == None:
        page = 1
    page_data = Newscol.query.join(
        News
    ).filter(
        Newscol.user_id == session['user_id']
    ).order_by(
        Newscol.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('home/newscol.html', page_data=page_data)


# 5.基于物品的协同过滤新闻推荐  对新闻的评分
@home.route('/newsrecommend', methods=['GET'])
@user_login_req
def newsrecommend():
    user_id = session['user_id']

    itemCF = ItemBasedCF()
    ratings = Rating.query.all()  # 查找所有的评分
    itemCF.get_dataset(ratings)  # 读取“用户-新闻”数据
    itemCF.calc_news_sim()  # 计算新闻相似度  无返回值
    itemCF.evaluate()  # 得出评价指标
    items = itemCF.recommend(user_id)  # 得到推荐结果
    # print(items)  # 对应的新闻id和推荐度
    page_data = []
    for id, score in items:
        rv = News.query.get(id)
        if rv is None:
            rv = News.query.get(1)
        page_data.append(rv)
    return render_template('home/newsrecommend.html', page_data=page_data)


# 6.基于用户的协同过滤新闻推荐
@home.route('/newsrecommend2', methods=['GET'])
@user_login_req
def newsrecommend2():
    user_id = session['user_id']

    userCF = UserBasedCF()
    ratings = Rating.query.all()
    userCF.get_dataset(ratings)
    userCF.calc_user_sim()
    userCF.evaluate()
    items = userCF.recommend(user_id)
    page_data = []
    for id,score in items:
        rv = News.query.get(id)
        if rv is None:
            rv = News.query.get(1)
        page_data.append(rv)
    return render_template('home/newsrecommend2.html', page_data=page_data)


# 添加新闻收藏(AJAX异步方法)
@home.route('/newscol/add/', methods=['GET'])
@user_login_req
def newscol_add():
    # 接受uid用户ID和mid新闻ID
    uid = request.args.get("uid", "")
    mid = request.args.get("mid", "")
    newscol = Newscol.query.filter_by(
        # user_id = int(uid),
        # news_id = int(mid)
        news_id=mid,
        user_id=uid
    ).count()
    if newscol == 1:  # 如果该用户已经收藏了该新闻
        data = dict(ok=0)
    # if newscol == 0:  #没有收藏就要收藏
    else:
        newscol = Newscol(
            news_id=mid,
            user_id=uid
        )
        db.session.add(newscol)
        db.session.commit()
        data = dict(ok=1)
    import json
    return json.dumps(data)  # 浏览器返回一个json:{"ok": 1}
    # return json.dumps(dict(ok=1))


# 搜索页面
@home.route('/search/<int:page>/')
def search(page=None):
    if page == None:
        page = 1
    key = request.args.get('key', '')  # 接受填入的key值,没有就是空
    # print(key)
    # 新闻信息
    page_data = News.query.filter(
        News.title.ilike('%' + key + '%')  # 模糊匹配
    ).order_by(
        News.id.asc()
    ).paginate(page=page, per_page=10)
    # 搜索个数
    news_count = News.query.filter(
        News.title.ilike('%' + key + '%')  # 模糊匹配
    ).count()
    page_data.key = key  # 把搜索的关键字key传入翻译的模板ui/search.html

    return render_template('home/search.html', key=key, page_data=page_data, movie_count=news_count)


# 新闻详情页
@home.route('/play/<int:id>/<int:page>/', methods=['GET', 'POST'])
def play(id=None, page=None):
    # form = CommentForm()
    news = News.query.get_or_404(id)
    tag = Tag.query.filter_by(id=news.tag_id).first()
    news.commentnum += 1
    form = StarForm()
    # 提交评级
    if 'user' in session and form.validate_on_submit():
        data = form.data['star']
        # print(data)
        # 添加评分
        rating = Rating(
            userid=session['user_id'],
            newsid=news.id,
            rating=data
        )
        r = Rating.query.filter_by(
            newsid=news.id,
            userid=session['user_id']
        ).first()
        if r:
            query = db.session.query(Rating)
            query.filter(Rating.newsid == news.id, Rating.userid == session['user_id']).update({Rating.rating: data})
        else:
            db.session.add(rating)
            db.session.commit()
    db.session.add(news)
    db.session.commit()

    # 获取当前用户对此新闻的评分
    if 'user' in session:
        r = Rating.query.filter_by(
            newsid=news.id,
            userid=session['user_id']
        ).first()
        if r:
            news.star = r.rating
            if news.star > 5:
                news.star = 5
        else:
            news.star = 0
    else:
        if news.star > 5:
            news.star = 5

    return render_template('home/play.html', news=news, tag=tag, form=form)


# 404页面 (去蓝图__init__.py中定义,而不是在这个视图中)

# 6.各类别新闻数量统计
@home.route('/data1', methods=['GET'])
@user_login_req
def data1():
    page_data = []
    db2 = pymysql.connect(host="127.0.0.1", port=33060, user="root", password="123456", db="news_db")
    cursor = db2.cursor()
    try:
        cursor.execute("select tag_id, count(*) as count from news group by tag_id")
        result = cursor.fetchall()  # 从数据库的游标中获取所有的查询结果
        # print(result)
        db2.commit()
        for r in result:
            dic = {}
            dic['xdata'] = Tag.query.filter_by(id=r[0]).first().name
            dic['ydata'] = r[1]
            page_data.append(dic)
            # print(dic)
    except:
        # 是Python标准库中的一个函数，用于将异常信息输出到标准错误流，通常用于调试和排查错误
        traceback.print_exc()
    cursor.close()
    db2.close()
    # [{'xdata': '资讯', 'ydata': 756}, {'xdata': '法制', 'ydata': 148}, {'xdata': '日报', 'ydata': 1576}, {'xdata': '环球', 'ydata': 537},
    # {'xdata': '晚报', 'ydata': 1398}, {'xdata': '财经', 'ydata': 111}, {'xdata': '人民', 'ydata': 1422}, {'xdata': '娱乐', 'ydata': 25},
    # {'xdata': '青年', 'ydata': 114}, {'xdata': '健康', 'ydata': 88}, {'xdata': '其他', 'ydata': 10731}]
    # print(page_data)
    return render_template('home/data1.html', page_data=page_data)


# 7.新闻浏览量排行榜
@home.route('/data2', methods=['GET'])
@user_login_req
def data2():
    page_data = []
    db2 = pymysql.connect(host="127.0.0.1", port=33060, user="root", password="123456", db="news_db")
    cursor = db2.cursor()
    try:
        cursor.execute("select id, commentnum from news order by commentnum desc limit 20")
        result = cursor.fetchall()
        db2.commit()
        for r in result:
            dic = {}
            dic['xdata'] = r[0]
            dic['ydata'] = r[1]
            page_data.append(dic)
    except:
        traceback.print_exc()
    cursor.close()
    db2.close()

    return render_template('home/data2.html', page_data=page_data)
