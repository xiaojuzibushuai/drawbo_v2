# -*- coding:utf-8 -*-
from flask import request, redirect, url_for, flash
from flask_admin import AdminIndexView, expose, helpers
from flask_security import login_user, logout_user, current_user
from sqlalchemy import text

from forms.login_form import LoginForm
from models.course import Category, Course, DeviceCourse
from models.device import Device
from models.user import User
from models.user_device import User_Device
from utils.tools import manager_app_logs
from sys_utils import db


class CustomAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        else:
            # 图表展示
            # 1、展示小程序登录总用户数
            all_user_count = User.query.count()
            # 2、展示已绑定用户数
            bind_user_count = User.query.filter(User.device > 0).count()
            # 3、展示总设备数
            all_dev_count = Device.query.count()
            # 4、展示总分类数
            all_cate_count = Category.query.count()
            # 5、展示总课程数
            all_course_count = Course.query.count()
            data = [all_user_count, bind_user_count, all_dev_count, all_cate_count, all_course_count]
            # 便捷工具
            # 1、批量设置设备课程次数
            # 2、批量设置设备分类锁
            # devices = Device.query.all()

            #20231123 xiaojuzi 修改  根据用户绑定的所有设备一键批量添加所有课程使用次数
            users = User.query.all()

            return self.render('index.html', data=data, users=users)

    @expose('/login/', methods=['GET', 'POST'])
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            # login.login_user(user)
            login_user(user)
            # logs
            manager_app_logs('user,login', '登录成功')
        if current_user.is_authenticated:
            return redirect(url_for('.index'))

        self._template_args['form'] = form

        return self.render('login.html')

    @expose('/logout/')
    def logout_view(self):
        manager_app_logs('user,logout', '退出登录')
        logout_user()
        return redirect(url_for('.index'))

    #xiaojuzi 20231123
    @expose('/set_course_count', methods=['POST'])
    def set_course_count(self):
        """
        设置课程数量（批量用）
        :return: bool
        """
        # device_id = request.form.get('device_id', 0)

        userid = request.form.get('user_id', 0)

        count1 = request.form.get('count', 0)
        manager_app_logs('set,data', 'set_course_count: userid(%s),count(%s)' % (userid, count1))

        # dc_list = DeviceCourse.query.filter_by(device_id=int(device_id)).all()

        sql_statement = text("UPDATE device_course d SET d.use_count = d.use_count + :count1 WHERE d.device_id IN ("
                         "SELECT id FROM device WHERE deviceid IN ("
                         " SELECT deviceid FROM user_device WHERE userid = :userid and is_choose=1)); ")

        db.session.execute(sql_statement, {"count1" : int(count1), "userid" : userid})

        db.session.commit()

        # dc_list = User_Device.query(User_Device.deviceid).filter_by(userid=userid).all()

        # device_str_id = ''
        # for dc in dc_list:
        #     if not device_str_id:
        #         device_str_id = dc.device.deviceid
        #     dc.use_count = dc.use_count+int(count)
        # db.session.commit()

        flash('设置成功: 用户(%s),次数加(%s)' % (userid, count1), 'success')
        return redirect(url_for('.index'))

