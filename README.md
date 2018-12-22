# Accesser
一个解决GFW通过[检测server_name](https://github.com/googlehosts/hosts/issues/87)导致中文维基、Pixiv等站点无法访问的工具  
[支持的站点](https://github.com/URenko/Accesser/wiki/目前支持的站点)

## 一键使用
### Windows
[点此进入下载页](https://github.com/URenko/Accesser/releases/latest)，下载Windows_x64.zip，解压后运行`start.bat`即可，首次运行可能会申请管理员权限  
[Firefox设置方法](https://github.com/URenko/Accesser/wiki/Firefox设置方法)

## 依赖
- Python3.7 (其他版本未测试)
- [pyopenssl](https://pyopenssl.org/)
- [sysproxy](https://github.com/Noisyfox/sysproxy)(for Windows)
- [doh-proxy](https://github.com/facebookexperimental/doh-proxy)

## 使用
- 启动服务器  
`python accesser.py`
- 更新服务器证书  
`python accesser.py -r`
- 更新根证书和服务器证书（部分平台需手动导入证书）  
`python accesser.py -rr`
- 增加支持的网址：  
按pac文件格式编辑`pac.txt`使要网址从代理过  
在`domains.txt`中添加新行再加入域名，重新启动程序

## 当前支持
|                   |Windows|Mac OS|Linux|
|-------------------|-------|------|-----|
|基础支持            |  ✔  |  ✔  | ✔ |
|自动配置pac代理      |  ✔  |      |     |
|自动导入证书至系统   |  ✔  |      |     |
|自动导入证书至Firefox|      |      |     |

## TODO
- [ ] Pixiv注册  
- [ ] 自动证书配置（不用domains.txt）