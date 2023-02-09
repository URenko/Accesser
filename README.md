# Accesser
[English version](README.en.md)

一个解决SNI RST导致维基百科、Pixiv等站点无法访问的工具  
[支持的站点](https://github.com/URenko/Accesser/wiki/目前支持的站点)

[![](https://img.shields.io/github/release/URenko/Accesser.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/downloads/URenko/Accesser/total.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/license/URenko/Accesser.svg)](https://github.com/URenko/Accesser/blob/master/LICENSE)

## 使用
### 如果不知道什么是Python
从[这里](https://github.com/URenko/Accesser/releases/download/v0.8.0/accesser.exe)下载Windows一键程序，运行既可，首次使用会要求安装证书，选是即可。
### 如果已经安装了Python 3.11*或更高版本
```
pip3 install -U accesser[doh]
```
如果你不需要DNS-over-HTTPS，则可以不用带`[doh]`。

然后通过如下命令启动：
```
accesser
```
对于Windows系统，默认情况下（没有指定`--notsetproxy`）会设置PAC代理为`http://localhost:7654/pac/?t=<随机数>`，如果没有可以手动设置。

此外，对于Windows系统，默认情况下（没有指定`--notimportca`）会自动导入证书至系统，如果没有可以手动导入，请看[这里](https://github.com/URenko/Accesser/wiki/FAQ#q-windows%E8%AE%BF%E9%97%AE%E7%9B%B8%E5%85%B3%E7%BD%91%E7%AB%99%E5%87%BA%E7%8E%B0%E8%AF%81%E4%B9%A6%E9%94%99%E8%AF%AF%E6%82%A8%E7%9A%84%E8%BF%9E%E6%8E%A5%E4%B8%8D%E6%98%AF%E7%A7%81%E5%AF%86%E8%BF%9E%E6%8E%A5neterr_cert_invalid%E4%B9%8B%E7%B1%BB%E7%9A%84%E6%80%8E%E4%B9%88%E5%8A%9E%E8%AF%81%E4%B9%A6%E5%AF%BC%E5%85%A5%E9%94%99%E8%AF%AF%E6%80%8E%E4%B9%88%E5%8A%9E%E5%A6%82%E4%BD%95%E5%8D%B8%E8%BD%BD%E8%AF%81%E4%B9%A6)。

#### *为什么所需的python最低版本是3.11?
为了能优雅地用协程将socket连接升级为TLS连接，需要[asyncio.StreamWriter.start_tls()](https://docs.python.org/zh-cn/3/library/asyncio-stream.html#asyncio.StreamWriter.start_tls)，这一功能到python 3.11才提供。

可以使用例如[pyenv](https://github.com/pyenv/pyenv)来安装python 3.11。

## 设置
编辑工作目录下的`config.toml`，具体含义见其中注释，保存后重新打开程序。

## 进阶1: 与v2ray等其他代理软件一起使用
Accesser是一个本地HTTP代理，默认代理地址为`http://localhost:7654`，只要网络流量能从其他代理软件以HTTP代理导出就能联合使用。

以[v2ray](https://github.com/v2fly/v2ray-core)为例，可以添加一个HTTP的outbound指向`http://localhost:7654`，并设置相应的路由规则，将维基百科、Pixiv等站点的流量送到这个outbound。

此外，你还可以设置一个DNS outbound，然后编辑`config.toml`让Accesser使用这一DNS。

## 进阶2: 增加支持的网站
编辑工作目录下的pac文件（如果是一键程序，可以从GitHub下载这一文件到工作目录），使要支持的网站从代理过。

然而，并不是所有站点都可以直接工作，可能需要一些调节，见[如何适配站点](https://github.com/URenko/Accesser/wiki/如何适配站点)。