from time import sleep
import pandas
import pymysql
from hashlib import sha512


def executeScriptsFromFile(filename):
    with open(filename, 'r') as fd:
        sql_file = fd.read()
    sql_commands = sql_file.split(';')
    for command in sql_commands:
        if command == '':
            continue
        try:
            cursor.execute(command)
        except Exception as error_message:
            print("Command skipped: ", error_message)


def dropTable(tableName):
    try:
        cursor.execute(f'drop table if exists {tableName};')
    except Exception as error_message:
        print("Command skipped: ", error_message)


conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    passwd='0000',
    db='iosclub',
    charset='utf8mb4',
)
cursor = conn.cursor()

dropTable("device_borrowed")
dropTable("device_list")
dropTable("day_off")
dropTable("class_state")
dropTable("rtc_state")
dropTable("comment")
dropTable("member_list")
dropTable("announcement")

executeScriptsFromFile('create_table.sql')

df = pandas.read_csv("member_list.csv").T
for i in range(df.shape[1]):
    seed = df[i][2] if df[i][9] == 'None' else df[i][9]
    pwd = sha512(seed.encode('utf-8')).hexdigest().upper()
    manager = df[i][10]
    val = (df[i][0], df[i][1], df[i][2], df[i][3], df[i][4],
           df[i][5], df[i][6], df[i][7], df[i][8], None, pwd, manager)
    print(val)
    sql = "insert into member_list VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0);"
    cursor.execute(sql, val)
conn.commit()

df = pandas.read_csv("punch_in.csv")
print(df)
sql = 'insert into class_state (member_id,date,attendance,register) values (%s,%s,%s,%s);'
for i in range(1, len(df.columns)):
    time = df.columns[i][:10].split('.')
    for line in df.values:
        Bool = str(line[i]).upper()
        att = 1 if Bool == 'TRUE' else 0
        rei = 0 if Bool == 'FALSE' else 1
        val = (line[0], f'{time[0]}-{time[1]}-{time[2]} 00:00:00', att, rei)
        print(val)
        try:
            cursor.execute(sql, val)
        except Exception as msg:
            print("Command skipped: ", msg)
conn.commit()

df = pandas.read_csv("announcement.csv").T
for i in range(df.shape[1]):
    val = (df[i][0], df[i][1], df[i][2], df[i][3], df[i][4], df[i][5])
    print(val)
    sql = "insert into announcement VALUE (%s,%s,%s,%s,%s,%s);"
    cursor.execute(sql, val)
conn.commit()

df = pandas.read_csv("device.csv")
for i in range(df.shape[0]):
    val = [j if j != 'NN' else None for j in list(df.values[i])]
    print(val)
    sql = "insert into device_list values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, val)
conn.commit()

df = pandas.read_csv('borrow.csv')
for i in range(df.shape[0]):
    sql = "insert into device_borrowed values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    val = [j if j != 'NN' else None for j in list(df.values[i])]
    print(val)
    cursor.execute(sql, val)
    # print(val)
conn.commit()
