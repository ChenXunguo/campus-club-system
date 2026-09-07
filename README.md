# 校园社团活动管理系统

基于 **Flask + MySQL + Bootstrap 5** 的 B/S 架构社团活动管理系统，实现活动发布、报名审核、扫码签到、总结归档的全流程线上化管理。依据《校园社团活动管理系统项目说明书》完整实现。

## 功能总览



| 模块      | 功能                                                               |
| ------- | ---------------------------------------------------------------- |
| 用户认证与权限 | 注册 / 登录（Flask-Login）、三级角色权限、个人信息管理、自定义 `role_required` 装饰器       |
| 活动发布与管理 | 发布 / 编辑 / 删除、状态流转（待发布 / 进行中 / 已结束 / 已取消）、列表搜索筛选、Quill 富文本详情、封面上传 |
| 报名与审核   | 在线报名 / 取消、状态流转（待审核→通过 / 拒绝）、防重复报名（唯一约束）、名单查看与 CSV 导出             |
| 签到统计    | 签到二维码动态生成（qrcode，10 分钟有效）、扫码 / 手动签到、签到率自动统计、数据 CSV 导出            |
| 总结归档    | 总结文本 + 附件上传、按学期 / 社团 / 关键词检索、归档详情查看                              |
| 社团与成员   | 社团创建 / 编辑、成员添加移除、管理员任命 / 解除、社团活动统计                               |

## 技术栈



* Python 3.8+（本机 3.14）

* Flask 2.3.3 / Flask-SQLAlchemy 3.1.1 / Flask-Login 0.6.2 / Flask-Migrate 4.0.4

* MySQL 5.7+ / 8.0（PyMySQL 驱动）

* qrcode + Pillow（二维码）

* HTML/CSS/JS + Bootstrap 5 + Quill.js（富文本）

> 说明：说明书要求 Pillow 10.0.0，因本机 Python 3.14 兼容性改为 
>
> `Pillow>=11.3.0`
>
> ，功能不受影响。

## 项目结构



```
campus-club-system/

├── app/

│   ├── \_\_init\_\_.py          # 应用工厂

│   ├── decorators.py        # role\_required 权限装饰器

│   ├── utils.py             # 文件上传工具

│   ├── models/              # 数据模型（user/club/activity/registration/checkin/archive）

│   ├── blueprints/          # 蓝图（auth/activity/registration/checkin/archive/admin）

│   ├── services/            # 业务逻辑层（Service）

│   ├── templates/           # HTML 模板（Bootstrap 5）

│   └── static/              # 静态资源与上传文件

├── scripts/init\_db.py       # 数据库初始化 + 种子数据

├── config.py                # 配置文件

├── requirements.txt

└── run.py                   # 启动文件
```

## 快速开始

### 1. 环境准备



```
python -m venv venv

\# Windows

venv\Scripts\activate

\# Linux / Mac

source venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置数据库

复制 `.env.example` 为 `.env`，填写 MySQL 连接信息：



```
DB\_USERNAME=root

DB\_PASSWORD=你的密码

DB\_NAME=club\_system
```

### 3. 初始化数据库



```
\# 创建数据库 + 建表 + 写入演示数据

python scripts/init\_db.py --seed
```

### 4. 启动



```
python run.py
```

浏览器访问 `http://localhost:5000`。

## 演示账号



| 角色           | 用户名      | 密码       |
| ------------ | -------- | -------- |
| 系统管理员        | admin    | admin123 |
| 社团管理员（篮球社）   | chenyu   | 123456   |
| 社团管理员（音乐社）   | linxiao  | 123456   |
| 社团管理员（志愿者协会） | wangfang | 123456   |
| 社团管理员（文学社）   | liuyang  | 123456   |
| 学生           | zhaomin  | 123456   |
| 学生           | qianlei  | 123456   |

## 核心页面路由



| 端     | 路由                                                                                                                                                                       |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 公共    | `/` 首页、`/login`、`/register`、`/activities` 活动广场                                                                                                                           |
| 学生    | `/activity/<id>` 详情、`/my-registrations` 我的报名、`/my-checkins` 签到记录、`/archives` 归档                                                                                          |
| 社团管理员 | `/admin/activities` 活动管理、`/admin/activity/create` 发布、`/admin/registrations` 报名审核、`/admin/checkin` 签到管理、`/admin/checkin/generate/<id>` 生成二维码、`/admin/archive/create` 总结上传 |
| 系统管理员 | `/admin/users` 用户管理、`/admin/clubs` 社团管理、社团详情 `/admin/club/<id>`（成员 / 任命 / 统计）                                                                                            |

## 数据库设计

6 张核心表：`user`、`club`、`activity`、`registration`、`checkin`、`archive`，字段设计严格遵循说明书 5.2 节。



* `registration` 增加唯一约束 `(activity_id, user_id)` 实现防重复报名

* `activity` 扩展 `checkin_code` / `checkin_expire` 两字段，支撑签到码动态生成与有效期控制

* 签到率 = 已签到人数 / 报名通过人数 × 100%

## 测试

功能测试用例覆盖说明书 8.2 节（登录、发布、权限、报名、审核、签到、归档、越权 403 等）。



```
\# 进入项目根目录，运行测试（使用独立测试库 club\_system\_test，不影响业务数据）

python -m pytest tests/ -v
```

**测试结果（2026-09-07 实测）：14/14 全部通过**



| 编号    | 测试用例           | 结果   |
| ----- | -------------- | ---- |
| TC-01 | 正确账号密码登录       | ✅ 通过 |
| TC-02 | 错误密码登录         | ✅ 通过 |
| TC-03 | 社团管理员发布活动      | ✅ 通过 |
| TC-04 | 普通学生发布活动（403）  | ✅ 通过 |
| TC-05 | 学生报名活动         | ✅ 通过 |
| TC-06 | 同一学生重复报名       | ✅ 通过 |
| TC-07 | 报名人数已达上限       | ✅ 通过 |
| TC-08 | 管理员审核通过报名      | ✅ 通过 |
| TC-09 | 管理员审核拒绝报名      | ✅ 通过 |
| TC-10 | 扫描签到二维码        | ✅ 通过 |
| TC-11 | 未报名用户扫码签到      | ✅ 通过 |
| TC-12 | 上传活动总结         | ✅ 通过 |
| TC-13 | 按学期检索归档        | ✅ 通过 |
| TC-14 | 学生访问管理员页面（403） | ✅ 通过 |

另已在真实运行环境完成端到端联调：注册 → 报名 → 审核 → 生成签到二维码 → 扫码签到 → 签到率统计，全部正常。

## Windows 快速启动

双击项目根目录的 `start.bat`，或在命令行执行：



```
venv\Scripts\python run.py
```

浏览器访问 `http://127.0.0.1:5000`（局域网设备可用 `http://本机IP:5000` 访问，便于手机扫码测试）。