# -*- coding: utf-8 -*-
"""
数据库初始化脚本：创建数据库、建表、写入演示种子数据
用法（在项目根目录执行）：
    python scripts/init_db.py            # 仅创建数据库并建表（不清数据）
    python scripts/init_db.py --seed      # 建表并写入演示数据
    python scripts/init_db.py --reset     # 删除旧表后重建（慎用）
数据库连接信息从 config.py / 环境变量 / .env 读取。
"""
import os
import sys
from datetime import datetime, timedelta

import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402


def get_dsn():
    """从配置读取数据库连接参数"""
    return {
        'host': Config.DB_HOST,
        'port': int(Config.DB_PORT),
        'user': Config.DB_USERNAME,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
        'charset': 'utf8mb4',
    }


def create_database():
    """连接 MySQL 服务器并创建目标数据库（若不存在）"""
    conn = pymysql.connect(host=Config.DB_HOST, port=int(Config.DB_PORT),
                           user=Config.DB_USERNAME, password=Config.DB_PASSWORD,
                           charset='utf8mb4')
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        print(f"[OK] 数据库 {Config.DB_NAME} 已就绪")
    finally:
        conn.close()


def seed_data():
    """写入演示种子数据"""
    from app import create_app, db
    from app.models.activity import Activity
    from app.models.archive import Archive
    from app.models.checkin import Checkin
    from app.models.club import Club
    from app.models.registration import Registration
    from app.models.user import User, ROLE_CLUB_ADMIN, ROLE_SYS_ADMIN

    app = create_app('development')
    with app.app_context():
        # 已存在数据则不重复写入
        if User.query.count() > 0:
            print('[SKIP] 数据库中已有用户数据，跳过种子写入。')
            return

        now = datetime.now()
        semester = f'{now.year}-{now.year + 1}-1'

        # ---------- 用户（阶段一：系统管理员）----------
        sys_admin = User(username='admin', real_name='系统管理员',
                         role=ROLE_SYS_ADMIN, email='admin@school.edu.cn')
        sys_admin.set_password('admin123')
        db.session.add(sys_admin)
        db.session.flush()  # sys_admin.id = 1

        # ---------- 社团（阶段二：先建社团，获得 id）----------
        clubs_data = [
            ('篮球社', '文体类', '以球会友，强身健体，组织校内外篮球交流与赛事。'),
            ('音乐社', '文体类', '汇聚音乐爱好者，开展演出、器乐与声乐交流活动。'),
            ('青年志愿者协会', '公益类', '践行志愿服务精神，组织社区服务与公益活动。'),
            ('文学社', '学术类', '以文会友，开展读书分享、征文比赛与创作交流。'),
        ]
        club_objs = []
        for name, cat, desc in clubs_data:
            club_objs.append(Club(name=name, category=cat, description=desc,
                                  founder_id=sys_admin.id))
        db.session.add_all(club_objs)
        db.session.flush()  # club_objs[i].id 已生成

        # ---------- 用户（阶段三：普通学生 + 社团管理员，引用社团 id）----------
        users = [
            # (username, real_name, student_id, role, password)
            ('zhaomin', '赵敏', '20230101', 'student', '123456'),
            ('qianlei', '钱磊', '20230102', 'student', '123456'),
            ('sunhao', '孙浩', '20230103', 'student', '123456'),
            ('lina', '李娜', '20230104', 'student', '123456'),
            ('zhouwei', '周伟', '20230105', 'student', '123456'),
        ]
        user_objs = []
        for i, (uname, real, sid, role, pwd) in enumerate(users):
            u = User(username=uname, real_name=real, student_id=sid, role=role,
                     club_id=club_objs[i % len(club_objs)].id)
            u.set_password(pwd)
            user_objs.append(u)

        # 社团管理员（分别担任不同社团）
        club_admins = [
            ('chenyu', '陈宇', '20220101', 0),   # 篮球社
            ('linxiao', '林晓', '20220102', 1),  # 音乐社
            ('wangfang', '王芳', '20220103', 2), # 志愿者协会
            ('liuyang', '刘洋', '20220104', 3),  # 文学社
        ]
        club_admin_objs = []
        for uname, real, sid, idx in club_admins:
            u = User(username=uname, real_name=real, student_id=sid,
                     role=ROLE_CLUB_ADMIN, club_id=club_objs[idx].id)
            u.set_password('123456')
            user_objs.append(u)
            club_admin_objs.append(u)

        db.session.add_all(user_objs)
        db.session.flush()

        # 设定社团创始人（社团管理员）
        for i, admin in enumerate(club_admin_objs):
            club_objs[i].founder_id = admin.id
        db.session.flush()

        # ---------- 活动 ----------
        base = now.replace(hour=14, minute=0, second=0, microsecond=0)
        activities_data = [
            # (club_idx, title, location, start, end, max, status, desc)
            (0, '秋季篮球友谊赛', '东区篮球场',
             base + timedelta(days=3), base + timedelta(days=3, hours=3), 30,
             'pending',
             '<p>面向全校的篮球友谊赛，欢迎大家报名参加，展示球技，以球会友！</p><ul><li>组队参赛</li><li>现场设观众席</li></ul>'),
            (1, '校园音乐节·迎新专场', '大学生活动中心',
             base + timedelta(days=5), base + timedelta(days=5, hours=4), 100,
             'pending',
             '<p>迎新专场音乐会，乐队、弹唱、合唱齐上阵，欢迎报名观演或上台献唱。</p>'),
            (2, '社区敬老志愿服务活动', '阳光社区',
             base + timedelta(days=1), base + timedelta(days=1, hours=5), 40,
             'ongoing',
             '<p>前往社区开展敬老服务：陪伴聊天、卫生打扫、义诊协助。</p>'),
            (3, '春日读书分享会', '图书馆报告厅',
             base - timedelta(days=7), base - timedelta(days=7, hours=2), 50,
             'ended',
             '<p>围绕“平凡的世界”开展读书分享，交流阅读感悟。</p>'),
            (0, '新生篮球入门训练营', '东区篮球场',
             base - timedelta(days=30), base - timedelta(days=30, hours=2), 20,
             'ended',
             '<p>为篮球新生开设的基础训练营，教练现场指导。</p>'),
            (2, '校园环保捡拾公益行动', '校园中心广场',
             base + timedelta(days=10), base + timedelta(days=10, hours=3), 60,
             'pending',
             '<p>清理校园公共区域垃圾，共建绿色校园。</p>'),
        ]
        activity_objs = []
        for (ci, title, loc, st, et, mx, status, desc) in activities_data:
            a = Activity(club_id=club_objs[ci].id, title=title, location=loc,
                         start_time=st, end_time=et, max_participants=mx,
                         status=status, description=desc,
                         publisher_id=db.session.get(Club, club_objs[ci].id).founder_id)
            db.session.add(a)
            activity_objs.append(a)
        db.session.flush()

        # ---------- 报名记录 ----------
        # 进行中活动（志愿者协会）：5 名学生报名，3 人通过并签到
        ongoing = activity_objs[2]
        students = User.query.filter_by(role='student').all()[:5]
        for i, stu in enumerate(students[:4]):
            reg = Registration(activity_id=ongoing.id, user_id=stu.id,
                               status='approved' if i < 3 else 'pending',
                               apply_time=now - timedelta(days=1))
            db.session.add(reg)
            if i < 3:
                reg.review_time = now - timedelta(hours=20)
                reg.reviewer_id = club_objs[2].founder_id
        db.session.flush()
        # 3 人扫码签到（其中 1 人迟到 30 分钟）
        for i, reg in enumerate(Registration.query.filter_by(
                activity_id=ongoing.id, status='approved').all()):
            ck = Checkin(registration_id=reg.id, activity_id=ongoing.id,
                         user_id=reg.user_id,
                         checkin_time=now - timedelta(hours=1) if i else now,
                         checkin_code='demo-' + str(reg.id), checkin_type='qr')
            db.session.add(ck)

        # 已结束活动（文学社读书会）：4 名学生报名，全部通过并签到
        ended = activity_objs[3]
        for i, stu in enumerate(students[:4]):
            reg = Registration(activity_id=ended.id, user_id=stu.id,
                               status='approved',
                               apply_time=now - timedelta(days=8),
                               review_time=now - timedelta(days=7),
                               reviewer_id=club_objs[3].founder_id)
            db.session.add(reg)
            db.session.flush()
            db.session.add(Checkin(registration_id=reg.id, activity_id=ended.id,
                                   user_id=stu.id,
                                   checkin_time=now - timedelta(days=7),
                                   checkin_code='demo-end', checkin_type='qr'))
        db.session.flush()

        # 待发布活动：部分学生报名（待审核）
        pending = activity_objs[0]
        for i, stu in enumerate(students[:2]):
            db.session.add(Registration(activity_id=pending.id, user_id=stu.id,
                                        status='pending',
                                        apply_time=now - timedelta(hours=3)))

        # ---------- 归档 ----------
        db.session.add(Archive(activity_id=ended.id,
                               summary=('<p>本次读书分享会共有 4 名同学参与，围绕'
                                        '《平凡的世界》展开了深入交流，现场氛围热烈。'
                                        '大家一致认为应多举办此类活动，营造阅读氛围。</p>'),
                               semester=semester,
                               archiver_id=club_objs[3].founder_id,
                               is_archived=True,
                               archive_time=now - timedelta(days=6)))
        db.session.flush()

        # 校正各活动 current_participants（统计有效报名数）
        for act in activity_objs:
            act.current_participants = Registration.query.filter(
                Registration.activity_id == act.id,
                Registration.status != 'cancelled').count()
        db.session.flush()

        db.session.commit()
        print('[OK] 种子数据写入完成')
        print('=' * 56)
        print('演示账号：')
        print('  系统管理员  admin    / admin123')
        print('  社团管理员  chenyu   / 123456（篮球社）')
        print('  社团管理员  linxiao  / 123456（音乐社）')
        print('  社团管理员  wangfang / 123456（志愿者协会）')
        print('  社团管理员  liuyang  / 123456（文学社）')
        print('  学生账号    zhaomin  / 123456')
        print('  学生账号    qianlei  / 123456')
        print('=' * 56)


def main():
    args = sys.argv[1:]
    do_reset = '--reset' in args
    do_seed = '--seed' in args

    if not Config.DB_PASSWORD:
        print('[!] 提示：未检测到数据库密码。请设置环境变量 DB_PASSWORD，'
              '或在项目根目录创建 .env 文件（参考 .env.example）。')
        print('[!] 当前数据库用户：', Config.DB_USERNAME)

    create_database()

    from app import create_app, db
    app = create_app('development')
    with app.app_context():
        if do_reset:
            # club 与 user 之间存在循环外键（说明书 5.2 设计所致），
            # 采用原生 SQL 按依赖顺序删除表并临时关闭外键检查
            with db.engine.begin() as conn:
                conn.execute(db.text('SET FOREIGN_KEY_CHECKS = 0'))
                for t in ('checkin', 'archive', 'registration',
                          'activity', 'user', 'club'):
                    conn.execute(db.text(f'DROP TABLE IF EXISTS `{t}`'))
                conn.execute(db.text('SET FOREIGN_KEY_CHECKS = 1'))
            print('[OK] 已删除所有旧表')
        db.create_all()
        print('[OK] 数据表创建完成')

    if do_seed:
        seed_data()

    print('完成。可使用以下命令启动：')
    print('  python run.py')


if __name__ == '__main__':
    main()
