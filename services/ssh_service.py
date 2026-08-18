import paramiko
from paramiko.ssh_exception import SSHException


class SSH:

    def __init__(self, **kwargs):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.kwargs = kwargs

    def __enter__(self):
        '''Как написать код для подключения к удаленному хосту с импрортируемым модулем paramiko'''
        kw = self.kwargs
        self.client.connect(hostname=kw.get('hostname'), username=kw.get('username'),
                            password=kw.get('password'), key_filename=(kw.get("pkey")), port=int(kw.get('port', 22)),
                            allow_agent=False,
                            timeout=5)
        transport = self.client.get_transport()
        if transport:
            # Отправляем пустой пакет каждые 30 секунд
            transport.set_keepalive(60)  # [citation:1][citation:3][citation:4]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def exec_cmd(self, cmd):
        ''' Необходимо выполнить команду с помощью скрипта (к прим. ls -al)'''
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=5)
            data = stdout.read()
            # print(f" ----> {stderr}")
            return stderr.read().decode()
        except SSHException as e:
            # if stderr:
            # raise stderr
            print(f"ERROR {e}")
        except Exception as e:
            print(f"ERROR {e}")
        finally:
            print("exec_cmd")
        # return data.decode()

    def check_ssh_tunnel(self) -> bool:
        transport = self.client.get_transport()
        print(f"tunnels ----------> transport {transport}")
        if transport is not None and transport.is_active():
            print(f"tunnels ----------> поднят")
            return True
        else:
            # await init_tunnel()
            print(f"tunnels --------- нееееееее подняь")
            return False