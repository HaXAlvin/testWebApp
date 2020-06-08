from base64 import b64encode
from datetime import timedelta, datetime
from os import path
from PIL import Image
from flask import Flask, render_template, request, jsonify, url_for, redirect
import flask_jwt_extended as jwt
from flask_apscheduler import APScheduler
import pyqrcode
from hashlib import sha256, sha512
import pymysql
from pandas import DataFrame
from bs4 import BeautifulSoup
from random import choice
from string import ascii_letters
from time import sleep
from io import BytesIO


class Config:
    # app set
    DEBUG = False
    HOST = '127.0.0.1'
    PORT = '5277'
    # jwt set
    JWT_SECRET_KEY = sha256("i05c1u652005505".encode('utf-8')).hexdigest()
    JWT_TOKEN_LOCATION = 'cookies'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=300)  # 逾期時間
    JWT_ALGORITHM = 'HS256'  # hash type
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'  # cookie name
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=300)
    JWT_ACCESS_COOKIE_PATH = '/'
    # db set
    DB_PORT = 3306
    DB_USER = 'root'
    DB_PWD = 'qwer25604677'
    DB_NAME = 'iosclub'
    DB_CHARSET = 'utf8mb4'
    # qrcode set
    QRCODE_LEN = 10
    QRCODE_EXPIRED = timedelta(minutes=3)
    # other set
    JOBS = [
        {
            'id': 'clean_record',
            'func': '__main__:clean_record',
            'misfire_grace_time': 60,
            'trigger': {
                'type': 'interval',
                'seconds': 3600  # clean timedelta
            }
        }
    ]


app = Flask(__name__)
app.config.from_object(Config())  # get setting
jwtAPP = jwt.JWTManager(app)
punch_record = []
img_path = path.dirname(path.abspath(__file__)) + '/static/img'
logos = [Image.open(img_path + f'/icon/icon0{i}.png') for i in range(1, 5)]
# print('key:', app.config['JWT_SECRET_KEY'])
while True:
    try:
        conn = pymysql.connect(
            host=app.config.get('HOST'),
            port=app.config.get('DB_PORT'),
            user=app.config.get('DB_USER'),
            passwd=app.config.get('DB_PWD'),
            db=app.config.get('DB_NAME'),
            charset=app.config.get('DB_CHARSET'),
        )
        break
    except pymysql.err as m:
        print(f'**{m}**')
        sleep(1)


def jwt_create_token(types, account):
    method = {'access': jwt.create_access_token,
              'refresh': jwt.create_refresh_token}
    return method[types](identity={'account': account}, headers={"typ": "JWT", "alg": "HS256"})


def run_sql_select(sql, val):  # only select
    try:
        conn.ping(reconnect=True)
        with conn.cursor() as cursor:
            cursor.execute(sql, val)
            res = cursor.fetchall()
            if not res:
                return None
            description = [i[0] for i in cursor.description]
            return {'res': res, 'des': description}
    except pymysql.err as msg:
        print(f'**{msg}**')
        return None


def run_sql_update(sql):
    try:
        conn.ping(reconnect=True)
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.err as msg:
        print(f'**{msg}**')
        return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    print(request.get_json())
    if not request.is_json:
        return jsonify({"login": False, "msg": "Missing JSON in request"}), 400
    account = request.json.get('account', None)
    password = request.json.get('password', None)
    if not account:
        return jsonify({"login": False, "msg": "Missing account parameter"}), 400
    if not password:
        return jsonify({"login": False, "msg": "Missing password parameter"}), 400
    sql = "SELECT member_nid,password,login_count FROM memberList WHERE member_nid = %s;"
    results = run_sql_select(sql, account)
    if results is None or sha512(password.encode('utf-8')).hexdigest().upper() != results['res'][0][1]:
        return jsonify({"login": False, "msg": "Bad account or password"}), 401
    access_token = jwt_create_token('access', account)
    refresh_token = jwt_create_token('refresh', account)
    get_next = request.json.get('next', None).replace('%2F', '/')
    if results['res'][0][2] == 0:
        next_page = 'enterIntroduce'
    else:
        next_page = '/' if not get_next else get_next
        res = run_sql_update(
            "UPDATE memberlist SET login_count = login_count+1")
        print(res)
    print(next_page)
    resp = jsonify({'login': True, 'next': next_page})
    # resp = redirect(url, code=302)
    jwt.set_access_cookies(resp, access_token)
    jwt.set_refresh_cookies(resp, refresh_token)
    return resp


@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/enterIntroduce', methods=['GET', 'POST'])
@jwt.jwt_optional
def enterIntroduce():
    identity = jwt.get_jwt_identity()
    print(identity)
    if not identity:
        return redirect(url_for('login', next='/enterIntroduce'))
    if request.method == 'GET':
        return render_template('enterIntroduce.html')
    data = request.get_json()
    sql = "SELECT member_nid,password,login_count FROM memberList WHERE member_nid = %s;"
    results = run_sql_select(sql, identity['account'])
    if results is None or sha512(data['pwd_old'].encode('utf-8')).hexdigest().upper() != results['res'][0][1]:
        return jsonify({"login": False, "msg": "Bad account or password"}), 401
    return


@jwtAPP.expired_token_loader  # 逾期func
def my_expired():
    resp = redirect(url_for('login', next=request.path))
    jwt.unset_jwt_cookies(resp)
    return resp, 302


@app.route('/searchName', methods=['POST'])
def search_name():
    conn.ping(reconnect=True)
    res = {'result': 'no'}
    sql = "SELECT * FROM memberList WHERE member_name LIKE %s;"
    val = '%' + request.json.get('data', None) + '%'
    results = run_sql_select(sql, val)
    if results is None:
        res['result'] = 'No data found'
    else:
        df = DataFrame(list(results['res']),
                       columns=results['des'])  # make a frame
        # turn into html table
        soup = BeautifulSoup(df.to_html(), 'html.parser')
        soup.find('table')['class'] = 'table'  # edit html
        res['result'] = soup.prettify()  # turn soup object to str
    return jsonify(res)  # 回傳json格式


@app.route('/query', methods=['POST'])
def query():
    conn.ping(reconnect=True)
    res = {'result': 'no'}
    try:
        with conn.cursor() as cursor:
            cursor.execute(request.json.get('data', None))
            conn.commit()
            results = cursor.fetchall()
            print(results)
            if not results:
                res['result'] = 'Success'
            else:
                df = DataFrame(list(results), columns=[
                               i[0] for i in cursor.description])  # make a frame
                # turn into html table
                soup = BeautifulSoup(df.to_html(), 'html.parser')
                soup.find('table')['class'] = 'table'  # edit html
                res['result'] = soup.prettify()  # turn soup object to str
    except Exception as error_message:
        res['result'] = str(error_message)
    return jsonify(res)  # 回傳json格式


@app.route('/search', methods=['GET'])
@jwt.jwt_optional
def search():
    identity = jwt.get_jwt_identity()
    print('search identity:', identity)
    if identity is None:
        redirect(url_for('login', next='/search'))
    return render_template('search.html')


# @app.route('/sign_up', methods=['GET'])
# def sign_up():
#     return render_template('sign_up.html')


@app.route('/create_qrcode', methods=['GET'])
@jwt.jwt_optional
def create_qrcode():
    identity = jwt.get_jwt_identity()
    if identity is None:
        return redirect(url_for('login', next='create_qrcode'))
    sql = 'SELECT member_nid, manager FROM memberlist where member_nid = %s;'
    results = run_sql_select(sql, identity['account'])
    if results is None:
        return 'error'
    accept = False if results['res'][0][1] == 0 else True
    if accept is False:
        return redirect(url_for('index'))
    code = ''.join(choice(ascii_letters)
                   for _ in range(app.config.get('QRCODE_LEN')))
    record = {'code': code, 'expired': datetime.now() +
              app.config.get('QRCODE_EXPIRED')}
    punch_record.append(record)
    url = f'/punch_in/{code}'
    qrcode = pyqrcode.create(
        f'{app.config.get("HOST")}:{app.config.get("PORT")}{url}', error='H')
    qrcode.png(img_path + '/qrcode.png', scale=14)  # 33*14
    img = Image.open(img_path + '/qrcode.png')
    img = img.convert("RGBA")
    icon_size = ((img.width ** 2) * 0.08) ** 0.5
    shapes = [int(img.width / 2 - icon_size / 2) if i <
              2 else int(img.width / 2 + icon_size / 2) for i in range(4)]
    img.crop(shapes)
    logo = choice(logos).resize((shapes[2] - shapes[0], shapes[3] - shapes[1]))
    logo.convert('RGBA')
    img.paste(logo, shapes, logo)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = b64encode(buffered.getvalue()).decode()

    return render_template('qrcode.html', qrcode=img_str, url=url)


@app.route('/punch_in/<code>')
@jwt.jwt_optional
def punch_in(code):
    identity = jwt.get_jwt_identity()
    if identity is None:
        return redirect(url_for('login', next='/punch_in/' + code))
    for record in punch_record:
        if code == record['code']:
            if datetime.now() <= record['expired']:
                punch_record.remove(record)
                return jsonify({'punch_in': punch_in_sql(identity['account'])})
            else:
                print('datetime expired')
                return jsonify({'punch_in': False})
    return jsonify({'punch_in': False})


def punch_in_sql(account):
    conn.ping(reconnect=True)
    try:
        with conn.cursor() as cursor:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "INSERT INTO class_state(member_id, date, attendance, register) " \
                  "VALUES((SELECT member_id FROM memberlist WHERE member_nid = %s), %s, 1, 1);"
            cursor.execute(sql, (account, now))
            results = cursor.fetchall()
            if not results:
                conn.commit()
                print(account, 'punch in at ', now, 'success')
                return True
            else:
                return False
    except pymysql.err.OperationalError as e:
        print(e)
        return False


@app.route('/punch_list', methods=['GET'])  # 個人出席
@jwt.jwt_optional
def punch_list():
    conn.ping(reconnect=True)
    identity = jwt.get_jwt_identity()
    if identity is None:
        return redirect(url_for('login', next='/punch_list'))
    sql = "SELECT date FROM class_state WHERE member_id = (SELECT member_id FROM memberlist WHERE member_nid = %s);"
    res = run_sql_select(sql, identity['account'])
    if res is None:
        return jsonify({'msg': 'fail'})
    else:
        df = DataFrame(res['res'], columns=res['des'])  # make a frame
        # turn into html table
        soup = BeautifulSoup(df.to_html(), 'html.parser')
        soup.find('table')['class'] = 'table'  # edit html
        soup = soup.prettify()  # turn soup object to str
        return soup


@app.route('/announcement', methods=['GET'])  # 公告
def announcement():
    # sql = 'SELECT * FROM announcement;'
    # res = run_sql_select(sql, ())
    # df = DataFrame(res['res'], columns=res['des'])
    # soup = BeautifulSoup(df.to_html(), 'html.parser')
    # # print(soup)
    # td_list = soup.find('tbody').find_all('td')
    # for i in range(2, len(td_list), 6):
    #     img = Image.open(img_path + f'/announcement/{td_list[i].contents[0]}.png')
    #     img = img.resize((100, 100), Image.BILINEAR)
    #     buffered = BytesIO()
    #     img.save(buffered, format="PNG")
    #     img_str = b64encode(buffered.getvalue()).decode()
    #     # td_list[i].contents[0] = img_str
    #     new_tag = soup.new_tag("img")
    #     new_tag['src'] = f"data:image/png;base64,{img_str}"
    #     # tag = f'<img src="data:image/png;base64,{img_str}">'
    #     td_list[i].string.replace_with(new_tag)
    #     print(str(td_list[i].contents[0]), type(td_list[i].contents[0]))
    # # print(soup.find('tbody').find_all('td'))
    # soup = soup.prettify()
    # print(soup)
    # return soup
    return render_template('announcement.html')


@app.route('/announcement_data', methods=['POST'])  # 出席
def announcement_data():
    sql = 'SELECT * FROM announcement;'
    res = run_sql_select(sql, ())
    if res is None:
        return jsonify(None)
    data = {'len': len(res['res']), 'src': [], 'alt': [],
            'title': [], 'content': [], 'view': [], 'date': []}
    for i in res['res']:
        data['date'].append(i[1].strftime("%Y/%m/%d %H:%M:%S"))
        data['alt'].append(i[2])
        data['title'].append(i[3])
        data['content'].append(i[4])
        data['view'].append(i[5])
        buffered = BytesIO()
        (Image.open(img_path +
                    f'/announcement/{i[2]}.png')).save(buffered, format="PNG")
        data['src'].append(b64encode(buffered.getvalue()).decode())
    print(data)
    return jsonify(data)


@app.route('/attendance', methods=['GET'])  # 出席
def attendance():
    conn.ping(reconnect=True)
    member_id = []
    member_name = []
    try:
        with conn.cursor() as cursor:
            sql = "SELECT member_id,member_name FROM memberlist;"
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                member_id.append(row[0])
                member_name.append(row[1])
            sql = "SELECT * FROM class_state;"
            cursor.execute(sql)
            results = cursor.fetchall()
    except pymysql.err.OperationalError as e:
        print(e)
        return e
    data = {'id': member_id, 'name': member_name}
    for row in results:
        row_date = row[2].strftime("%Y-%m-%d")
        if row_date not in data.keys():
            data[row_date] = ["-" for _ in range(len(member_id))]
        update_index = data['id'].index(row[1])
        if (row[3], row[4]) in [(1, 1), (1, 0)]:
            data[row_date][update_index] = 'O'
        elif (row[3], row[4]) == (0, 1):
            data[row_date][update_index] = 'LEAVE'
        else:
            data[row_date][update_index] = '-'
    dataFrame = DataFrame(data)
    # turn into html table
    soup = BeautifulSoup(dataFrame.to_html(), 'html.parser')
    # soup.find('table')['class'] = 'table'  # edit html
    return soup.prettify()


@app.route('/ChangePassword', methods=['GET'])
def ChangePassword():
    return render_template('ChangePassword.html')


def clean_record():  # clean qrcode list every specific time
    now_time = datetime.now()
    print(f"**Start Clean at {now_time}**")
    for records in punch_record:
        if records['expired'] > now_time:
            print(f"**Clean {records['code']} record**")
            punch_record.remove(records)
    now_time = datetime.now()
    print(f"**Ended Clean at {now_time}**")


if __name__ == '__main__':
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run(port=app.config.get('PORT'), host=app.config.get('HOST'))

# CSRF refresh
# @app.route('/refresh', methods=['POST'])
# @jwt_refresh_token_required
# def refresh():
#     # verify_jwt_refresh_token_in_request()
#     print(1111111111111111111111111111111)
#     identity = get_jwt_identity()
#     print(identity)
#     resp = jsonify({'login': True})
#     new_token = create_access_token(
#         identity={
#             'account': identity['account']
#         },
#         headers={
#             "typ": "JWT",
#             "alg": "HS256"
#         }
#     )
#     set_access_cookies(resp, new_token)
#     return jsonify(resp), 200
