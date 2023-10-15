#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import commands
import shutil
import logging
import signal

# 文件 deploy_log_file 里包含
# 1、升级的包名
# 2、升级的版本号
# 3、升级开始写入状态
# 4、升级结束后 由manager清空内容
# 监测系统的信号 获取后读取deploy_log_file中的包名和版本号

# 部署脚本工作相关的目录
# 目标目录        dest ==>  /ams/{服务名}
# 每个服务解压文件目录的临时目录 cd ==>  /ams/tmp
# 解压部署包的目录  /ams/resource
# 部署状态临时文件  /ams/.deploy.txt
# 部署包可以是完整路径的包名，也可以是在resource 目录下的文件名
import time

base_dir = "/ams"
dir_packages = os.path.join(base_dir, "resource")
service_script = os.path.join(base_dir, "manager/scripts/service/service.sh")
package_dir = os.path.join(dir_packages, "ams")  # /ams/resource/ams
deploy_log_file = os.path.join(dir_packages, ".deploy.txt")
json_file = os.path.join(package_dir, "package.json")

service = ["manager", "demultiplexer", "dmcu", "h323-mediagw", "h323-siggw",
           "ivr", "nmst", "sip-server", "frontend"]
all_server = {"manager": "",
              "demultiplexer": "",
              "dmcu": "usr/craft/relayserver",
              "h323-mediagw": "usr/craft/relayserver",
              "h323-siggw": "usr/gateway",
              "ivr": "usr/craft/relayserver",
              # "nginx": "",
              "nmst": "usr/craft/relayserver",
              "sip-server": "usr/sipproxy",
              "frontend": "frontend",
              }

logger = logging.getLogger('AMS-deploy')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(os.path.join(dir_packages, "deploy.log"))
fh.setLevel(logging.DEBUG)
# 创建Formatter对象
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
fh.setFormatter(formatter)
# 将FileHandler对象添加到Logger对象中
logger.addHandler(fh)


class DeployException(Exception):
    def __init__(self, num, setup, message):
        self.message = message
        self.setup = setup
        self.num = num

    def __str__(self):
        return "【{}】. deploy【{}】error:【{}】".format(self.num, self.setup, self.message)


# 执行shell ,返回结果是元组(返回码，输出结果)
# 执行正常时，返回码为0，输出结果为标准输出
# 执行异常时，返回码非0，输出结果为错误输出
def run_shell(cmd):
    return commands.getstatusoutput(cmd)


# 停止服务 systemctl stop xxx -> bool
def service_stop(service):
    cmd = "{} stop {}".format(service_script, service)
    return run_shell(cmd)


# 启动服务 systemctl stop xxx -> bool
def service_start(service):
    cmd = "{} start {}".format(service_script, service)
    return run_shell(cmd)


# reload服务 systemctl reload xxx -> bool
def service_reload(service):
    cmd = "{} reload {}".format(service_script, service)
    return run_shell(cmd)


# 查看服务的状态， running, dead, -> str
def service_status(service):
    cmd = "{} status {}".format(service_script, service)
    return run_shell(cmd)


# 参数校验,检验包名(绝对路径)是否存在，且符合规则 -> bool
def __check_arg_pack(abs_filename):
    return os.path.exists(abs_filename)


# 如果存在这个目录就返回True
def __check_dir_isexist(path):
    if os.path.exists(path) and os.path.isdir(path):
        return True
    return False


class Deploy(object):
    def __init__(self, package_name):
        self._package = package_name
        self.service = service
        self._tmp = os.path.join(base_dir, "tmp")
        self.service_data = []  # package json解析相应的服务版本及 文件名
        self.component_data = []

    # 加载json文件,读取相应服务和包名
    def load_json(self, package_file):
        try:
            with open(package_file, "r") as f:
                data = json.load(f)
            logger.info(data)
            for update_server_info in data["services"]:
                if update_server_info["name"] in self.service:
                    self.service_data.append(update_server_info)
            logger.info("所有待升级的服务信息：{}".format(self.service_data))
            if len(data["components"]) > 0:
                for component in data["components"]:
                    self.component_data.append(component)
            logger.info("所有待升级的组件信息：{}".format(self.component_data))
            return True
        except Exception as e:
            logger.error("读取json文件错误: " + e.message)
            return False

    # 服务列表是否在包含的服务列表之中 ,服务名是否会增加，服务是否会变化 -> bool
    def check_arg_service(self):
        not_in_service = []
        for service in self.service:
            if service not in all_server.keys():
                not_in_service.append(service)
        if len(not_in_service) > 0:
            logger.error("检测到异常服务名：" + str(not_in_service))
            return False
        return True

    @staticmethod
    def delete_dir(abs_path):
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            logger.info("清理目录{}".format(abs_path))
            shutil.rmtree(abs_path)

    # 把文件移动到部署目录中去
    def __deploy(self, dest, basedir=""):
        cmd = "mv {} {}".format(basedir if basedir != "" else "*", dest)
        logger.info("正在部署:" + cmd)
        self.delete_dir(dest)
        ok, out = run_shell(cmd)
        if ok != 0:
            logger.info("部署服务到目标目录时异常,返回码是【{}】错误是【{}】".format(ok, out))
            return False
        return True

    # 解开压缩包，rpm/zip/tar.gz
    @staticmethod
    def un_packing(source_pack_name, p_type):
        if p_type == "rpm":
            cmd = "rpm2cpio {} | cpio -div".format(source_pack_name)
        elif p_type == "zip":
            cmd = "unzip {} -d .".format(source_pack_name)
        elif p_type == "gz":
            cmd = "tar -axf {} ".format(source_pack_name)
        else:
            logger.error("部署包扩展名{}，不符合预期".format(source_pack_name))
            return False
        logger.info("正在解压缩部署包：" + cmd)
        ok, out = run_shell(cmd)
        if ok != 0:
            logger.error("解压包时出错：" + str(out))
            return False
        return True

    # 解压并部署
    def deploy_rpm(self, source_pack_name, dest, basedir=""):
        logger.info("把{}的{}目录部署到{}".format(source_pack_name, basedir, dest))
        self.__cd_tmp()
        p_type = self.__get_file_type(source_pack_name)
        if self.un_packing(source_pack_name, p_type):
            logger.info("解压包{}完成".format(source_pack_name))
            if self.__deploy(dest, basedir):
                logger.info("部署包{}正常完成".format(source_pack_name))
                return True
            else:
                logger.error("部署包{}时候出错".format(source_pack_name))
                return False
        else:
            logger.error("解压包{}时候出错".format(source_pack_name))
            return False

    # 确认文件的类型
    @staticmethod
    def __get_file_type(file_path):
        file_extension = os.path.splitext(file_path)[-1].lower()
        if file_extension == ".zip":
            return "zip"
        elif file_extension == ".gz":
            return "gz"
        elif file_extension == ".rpm":
            return "rpm"
        else:
            return "-"

    # 先清空临时目录，再创建并进入目录中
    def __cd_tmp(self):
        if os.path.exists(self._tmp):
            self.delete_dir(self._tmp)
            logger.info("清理临时目录: " + self._tmp)
        os.mkdir(self._tmp, 0755)
        os.chdir(self._tmp)


class DeployStatus(object):
    def __init__(self, out_file):
        self.__out_file = out_file
        self.data = {}

    def __write_line(self):
        data = self.__data2str()
        with open(self.__out_file, "w") as f:
            f.write(data)
            f.flush()

    def read_date(self):
        with open(self.__out_file, "r") as f:
            lines = f.readlines()
            for line in lines:
                logger.info("读取到数据:【{}】.".format(line))
                self.__str2data(line)

    def __str2data(self, str_data):
        if isinstance(str_data, str):
            str_list = str_data.split("=")
            if len(str_list) == 2:
                key = str_list[0].strip()
                value = str_list[1].replace('"', '').strip()
                self.data[key] = value
                logger.info("数据加载成功：【{}】.【{}】".format(key, value))

    def set_data(self, service, status):
        self.data[service] = status
        self.__write_line()

    def __data2str(self):
        re = ""
        key_list = self.data.keys()
        for key, value in self.data.items():
            # logger.info(key, value)
            if key == self.data[key_list[len(key_list) - 1]]:
                re += '{0}="{1}"'.format(key, value)
            else:
                re += '{0}="{1}"\n'.format(key, value)
        return re

    def reset_data(self):
        for key in all_server.keys():
            self.data[key] = 0
        self.data["last"] = 0
        logger.info('reset deploy.txt ok')
        self.__write_line()


def deploy(package):
    try:
        a = Deploy("package.tar.gz")
        # 1 检测包名
        if not str(a.check_arg_service()):
            raise DeployException(1, "检测部署包", "检测失败")
        logger.info("1 check package name ok")
        # 2 把tar包给解压开
        os.chdir(dir_packages)
        if not os.path.exists(package):
            package = os.path.join(dir_packages, package)
        if not a.un_packing(package, "gz"):
            raise DeployException(2, "解压部署包", "解压异常")
        logger.info("2 unpack ok")
        # 3 读取json文件
        if not a.load_json(json_file):
            raise DeployException(3, "加载描述文件", "异常")
        logger.info("3 load spec json file ok")
        # 单独设置组件的初始部署状态
        if len(a.component_data) > 0:
            for component in a.component_data:
                statFile.set_data(component["name"], 0)
        n = 0
        # 4 开始部署
        for update_server in a.service_data:
            n += 1
            mini_sid = "4-{}".format(n)
            name = update_server["name"]
            package = update_server["package"]
            statFile.set_data(name, 1)
            if name != "frontend":
                ok, out = service_stop(name)
                if ok != 0:
                    raise DeployException(mini_sid, name, "停止服务异常：" + out)
                logger.info("停止服务【{}】成功".format(name))
            logger.info("{} 正在部署{}...".format(mini_sid, name))
            ok = a.deploy_rpm(os.path.join(package_dir, name, package), os.path.join(base_dir, name), all_server[name])
            logger.info('{} deploy {} ,status: {}'.format(mini_sid, name, ok))
            if ok:
                statFile.set_data(name, 2)
                logger.info("{} 部署{}成功".format(mini_sid, name))
                if name != "frontend":
                    if name == "h323-siggw":
                        # h323-siggw, 部署完代码后，把包里的conf/*覆盖到/etc/ams/h323-siggw/下
                        run_shell("cp -ra /ams/h323-siggw/conf/* /etc/ams/h323-siggw/")
                    if name == "sip-server":
                        # 1. 部署前，把包里的conf/*覆盖到/etc/ams/h323-siggw/下
                        # 2. 删除/ams/ams/sip-server/conf目录
                        # 3. 创建软链接，ln -s /etc/ams/sip-server /ams/sip-server/conf
                        run_shell("cp -ra /ams/sip-server/conf/* /etc/ams/sip-server/")
                        run_shell("rm -rf /ams/sip-server/conf")
                        run_shell("ln -s /etc/ams/sip-server /ams/sip-server/conf")
                    ok, out = service_start(name)
                    if ok != 0:
                        raise DeployException(mini_sid, name, "启动服务异常：" + out)
                    logger.info("启动服务【{}】成功".format(name))
                else:
                    ok, out = run_shell("/ams/manager/scripts/initial/replace_frontend_ip.sh")
                    if ok != 0:
                        raise DeployException(mini_sid, "替换ip", "替换前端的ip异常：" + out)
                    logger.info("替换【前端ip】成功".format(name))
                    ok, out = service_reload("nginx")
                    if ok != 0:
                        raise DeployException(mini_sid, "nginx", "启动服务异常：" + out)
                    logger.info("重载【nginx】成功".format(name))
            else:
                logger.info("{} 部署{}失败".format(mini_sid, name))
                statFile.set_data(name, 3)
                raise DeployException(mini_sid, name, "部署失败，正在终止")
            a.delete_dir(os.path.join(base_dir, "tmp"))
            ok, out = service_status(name)
            if ok != 0:
                raise DeployException(mini_sid, name, "服务状态检测异常：" + out)
            logger.info("服务状态检测【{}】成功：{}".format(name, out))
            if name == "manager":
                time.sleep(10)
        logger.info("-------服务部署成功------")
        # 5 组件升级
        ok, start = update_component(a.component_data, "installer", len(a.component_data))
        if not ok:
            statFile.set_data("last", 3)
            logger.warning("组件升级失败，正在回滚组件...")
            ok, n = update_component(a.component_data, "restore", start)
            if not ok:
                logger.error("回滚组件失败")
            return
        statFile.set_data("last", 2)
        logger.info("-------组件部署成功------")
    except Exception as exp:
        logger.error("部署异常结束：" + exp.message)
        statFile.set_data("last", 3)
    finally:
        a.delete_dir(package_dir)


# 组件升级action(installer,restore)，返回元组，是否全部执行成功，成功执行的数量
def update_component(component_data, action, end):
    n = 0
    for component_item in component_data[:end]:
        n += 1
        mini_sid = "5-{}".format(n)
        name = component_item["name"]
        statFile.set_data(name, 1)
        script_name = os.path.join(package_dir, name, component_item[action])
        ok, out = run_shell(script_name)
        logger.info("{} 组件【{}】升级结果 状态码：{} out:{}".format(mini_sid, name, ok, out))
        if ok != 0:
            statFile.set_data(name, 3)
            logger.error("{} 组件【{}】升级失败！！！".format(mini_sid, name))
            return False, n
        statFile.set_data(name, 2)
        logger.info("{} 组件【{}】升级成功".format(mini_sid, name))
    return True, n


def main():
    # 加载数据文件
    statFile.read_date()
    statFile.reset_data()

    # 校验包名
    packagePathName = statFile.data.get("packagePathName")
    version = statFile.data.get("version")
    if packagePathName and version:
        logger.info("解析数据成功： packagePathName:【{}】,version:【{}】".format(packagePathName, version))
        deploy(packagePathName)
    else:
        logger.warning("解析数据失败，停止部署。 ")
        return


statFile = DeployStatus(deploy_log_file)

if __name__ == '__main__':
    main()