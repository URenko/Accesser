# Accesser
[中文版本](README.md)

A tool that solves SNI RST, which blocks sites like Wikipedia and Pixiv on the main land of China.

Because the main users of this project are in mainland China, you may encounter a lot of Chinese. Google translate may help you.

[Supported sites](https://github.com/URenko/Accesser/wiki/目前支持的站点)

[![](https://img.shields.io/github/release/URenko/Accesser.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/downloads/URenko/Accesser/total.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/license/URenko/Accesser.svg)](https://github.com/URenko/Accesser/blob/master/LICENSE)

*Welcome to participate[[Poll] Is it necessary to keep the web UI](https://github.com/URenko/Accesser/discussions/110)*

## One Click Usage
Download it from [here](https://github.com/URenko/Accesser/releases/download/v0.7.0/accesser.exe) and run it. The first time you use it, you will be asked to install a certificate, just select yes.

## Installing dependencies
- Python3.11*

and the following python libraries:
- `pyopenssl`: for generating certificates
- `dnspython`: for DNS queries
- `tld`: for auxiliary certificate generation

Install them with `pip install -r requirements.txt`

To use DNS-over-HTTPS, you need
- `httpx`

Install it with `pip install httpx[http2]`

### * Why is the minimum version of python required 3.11?
I know that e.g. the default python version of now widely used Ubuntu 22.04 LTS is 3.10, but in order to gracefully upgrade a socket connection to a TLS connection using coroutines, you need [asyncio.StreamWriter.start_tls()](https://docs.python.org/zh-cn/3/library/asyncio-stream.html#asyncio.StreamWriter.start_tls), which is not available until python 3.11.

You can use, for example, [pyenv](https://github.com/pyenv/pyenv) to install python 3.11.

## Launch
```
python3 accesser.py
```
For Windows, by default (without specifying `-notsetproxy`) it will set the system PAC proxy to `http://localhost:7655/pac/?t=<random number>`, if not you can set it manually.

In addition, for Windows, by default the certificate will be imported to the system automatically, if not you can import it manually, please see [here](https://github.com/URenko/Accesser/wiki/FAQ#q-windows%E8%AE%BF%E9%97%AE%E7%9B%B8%E5%85%B3%E7%BD%91%E7%AB%99%E5%87%BA%E7%8E%B0%E8%AF%81%E4%B9%A6%E9%94%99%E8%AF%AF%E6%82%A8%E7%9A%84%E8%BF%9E%E6%8E%A5%E4%B8%8D%E6%98%AF%E7%A7%81%E5%AF%86%E8%BF%9E%E6%8E%A5neterr_cert_invalid%E4%B9%8B%E7%B1%BB%E7%9A%84%E6%80%8E%E4%B9%88%E5%8A%9E%E8%AF%81%E4%B9%A6%E5%AF%BC%E5%85%A5%E9%94%99%E8%AF%AF%E6%80%8E%E4%B9%88%E5%8A%9E%E5%A6%82%E4%BD%95%E5%8D%B8%E8%BD%BD%E8%AF%81%E4%B9%A6).

## Advanced Usage 1: Use with other proxy software such as v2ray
Accesser is a local HTTP proxy with a default proxy address of `http://localhost:7655`, which can be used in combination with other proxy software as long as the network traffic can be exported as HTTP proxy.

Take [v2ray](https://github.com/v2fly/v2ray-core) as an example, you can add an HTTP outbound pointing to `http://localhost:7655` and set the corresponding routing rules to send traffic from sites like Wikipedia, Pixiv, etc. to this outbound.

In addition, you can set up a DNS outbound and then edit `config.json` to allow Accesser to use this DNS.

## Advanced Usage 2: Add sites
Copy `template/pac` to the same directory as `accesser.py` (if it is a one click program, you can download this file from GitHub and put it in the same directory as the exe), and edit the pac file to make the sites you want to support pass from the proxy.

However, not all sites will work straight away and may require some adjustment, see [How to adapt sites](https://github.com/URenko/Accesser/wiki/如何适配站点).