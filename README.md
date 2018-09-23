# Accesser
一个解决GFW通过[检测server_name](https://github.com/googlehosts/hosts/issues/87)导致中文维基、Pixiv等站点无法访问的工具

## 一键使用
### Windows
[点此下载](https://github.com/URenko/Accesser/releases/download/v0.4.7/Windows_x64.exe)，解压后运行`start.bat`即可，首次运行可能会申请管理员权限

## 依赖
- Python3.7 (其他版本未测试)
- [pyopenssl](https://pyopenssl.org/)

## 使用
- 启动服务器  
`python accesser.py`
- 更新服务器证书  
`python accesser.py -r`
- 更新根证书和服务器证书（部分平台需手动导入证书）  
`python accesser.py -rr`
- 增加支持的域名：  
在`domains.txt`中添加新行再加入域名，重新启动程序

## 当前自动导入证书支持
- [x] Windows
- [ ] Mac OS
- [ ] Linux
