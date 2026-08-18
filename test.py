# from sshtunnel import SSHTunnelForwarder  # Run pip install sshtunnel
# from sqlalchemy.orm import sessionmaker  # Run pip install sqlalchemy
# from sqlalchemy import create_engine
# # import psycopg2
# from sqlalchemy import text
#
# with SSHTunnelForwarder(
#         ('155.212.171.8', 22),  # Remote server IP and SSH port
#         ssh_username="postgres",
#         ssh_pkey="/Users/kril/.ssh/ed25519_vds_postgres",
#         # ssh_password="/Users/kril/.ssh/id_rsa_fincoin_kril",
#         ssh_password="Kril1966",
#         # remote_bind_address=('155.212.171.8', 5432)) as server: #PostgreSQL server IP and sever port on remote machine
#         remote_bind_address=('127.0.0.1', 5432)) as server:  # PostgreSQL server IP and sever port on remote machine
#
#     server.start()  # start ssh sever
#     print('Server connected via SSH')
#
#     # connect to PostgreSQL
#     local_port = str(server.local_bind_port)
#     print(local_port)
#     engine = create_engine('postgresql://postgres:Kril1966@127.0.0.1:' + local_port + '/greened')
#
#     Session = sessionmaker(bind=engine)
#     session = Session()
#
#     print('Database session created')
#
#     # test data retrieval
#     query = 'SELECT * FROM users'
#     test = session.execute(text(query))
#     for row in test:
#         print(row)
#
#     session.close()
from paramiko.ssh_exception import SSHException

from config import settings

# def original(value):
#     print(f" оригинал :{value} ")
#
#
# def one(fun):
#     print("one")
#
#     def two():
#         fun()
#         print("ywo")
#
#     return two
#
#
# print("11111")
# original(100) = one(original)
#
#
# def original(value):
#     print(f" оригинал :{value} ")
#
#
# def logging(func):
#     def inner(value):
#         print(" до вызова ")
#
#         func(value)
#
#         print(" пoceл вызова ")
#
#     return inner
#
#
# def retry(value):
#     def retry_d(func):
#         def _wrapper(*args, **kwargs):
#             for _ in range(value):
#                 print("Повтор")
#         return _wrapper
#     return retry_d
#
#
#
# @retry(3)
# def ddd():
#     print("ddddddd")
#
#
# ddd()
#
# original1 = logging(original)
# original1(" пример ")

# -*- coding: UTF-8 -*-
import paramiko

from services.ssh_service import SSH

if __name__ == '__main__':
    import json

    # Открываем файл для чтения
    with open("pool.json", "r", encoding="utf-8") as f:
        # Загружаем данные из файла в переменную
        data = json.load(f)

    print(data, "\n")
    print(data["questions"][0]["questions"])
    for a in data["questions"][0]["answers"]:
        print(a, "\n")

    # DB_USER_VDS = "postgres"
    # DB_PASS_VDS = "Kril1966"
    # DB_HOST_VDS = "155.212.171.8"
    # SSH_PORT = 22
    # # SSH_USERNAME = postgres
    # # SSH_PASSWORD = Kril1966
    # SSH_PKEY_PATH = "/Users/kril/.ssh/ed25519_vds_postgres"
    # with SSH(hostname=DB_HOST_VDS,
    #          username=DB_USER_VDS,
    #          password=DB_PASS_VDS,
    #          pkey=SSH_PKEY_PATH,
    #          port=22) as ssh:  # noob@10.0.1.**
    #     out = ssh.exec_cmd('ls -al /var')
    #     print(out)
    #     # print(out, file=open('log.log', 'a'))  # и записью вывода в лог
    # with SSH(hostname=DB_HOST_VDS,
    #          username=DB_USER_VDS,
    #          password=DB_PASS_VDS,
    #          pkey=SSH_PKEY_PATH,
    #          port=22) as ssh:  # noob@10.0.1.**
    #     out = ssh.exec_cmd('ls -al /var')
    #     print(out)
