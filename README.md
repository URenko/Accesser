# Accesser
[English version](README.en.md)

一个解决SNI RST导致维基百科、Pixiv等站点无法访问的工具  
[支持的站点](https://github.com/URenko/Accesser/wiki/目前支持的站点)

[![](https://img.shields.io/github/release/URenko/Accesser.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/downloads/URenko/Accesser/total.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/license/URenko/Accesser.svg)](https://github.com/URenko/Accesser/blob/master/LICENSE)

- 由于在可预见的时间内作者无时间与精力持续维护，本项目无限期断更
- 但是通过修改配置文件，在很长的时间里依然可用（实际上本项目的原理两年来没变过）
- 不建议使用nginx等有中间人攻击风险的方法（还记得最近github那件事吗）
- 如果追求更新，[GotoX](https://github.com/SeaHOH/GotoX/wiki/%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A8%E4%BC%AA%E9%80%A0-SNI-%E7%9A%84%E5%8A%9F%E8%83%BD)是一个不错的选择

## 使用方法
参见[https://urenko.github.io/Accesser/](https://urenko.github.io/Accesser/)

## 依赖
- Python3.7 (其他版本未测试)
- [pyopenssl](https://pyopenssl.org/)
- [sysproxy](https://github.com/Noisyfox/sysproxy)(for Windows)
- dnspython
- tornado
- tld

## 增加支持的网站 
按pac文件格式编辑`template/pac`使要支持的网站从代理过  

## 当前支持
|                   |Windows|Mac OS|Linux|
|-------------------|-------|------|-----|
|基础支持            |  ✔  |  ✔  | ✔ |
|自动配置pac代理      |  ✔  |      |     |
|自动导入证书至系统   |  ✔  |      |     |
