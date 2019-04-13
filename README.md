# Accesser
一个解决SNI RST导致中文维基、Pixiv等站点无法访问的工具  
[支持的站点](https://github.com/URenko/Accesser/wiki/目前支持的站点)

[![](https://img.shields.io/github/release/URenko/Accesser.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/downloads/URenko/Accesser/total.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/license/URenko/Accesser.svg)](https://github.com/URenko/Accesser/blob/master/LICENSE)

## 使用方法
参见[https://urenko.github.io/Accesser/](https://urenko.github.io/Accesser/)

## 依赖
- Python3.7 (其他版本未测试)
- [pyopenssl](https://pyopenssl.org/)
- [sysproxy](https://github.com/Noisyfox/sysproxy)(for Windows)
- [doh-proxy](https://github.com/facebookexperimental/doh-proxy)
- tornado
- tld

## 增加支持的网站 
按pac文件格式编辑`pac.txt`使要支持的网站从代理过  

## 当前支持
|                   |Windows|Mac OS|Linux|
|-------------------|-------|------|-----|
|基础支持            |  ✔  |  ✔  | ✔ |
|自动配置pac代理      |  ✔  |      |     |
|自动导入证书至系统   |  ✔  |      |     |
|自动导入证书至Firefox|      |      |     |
