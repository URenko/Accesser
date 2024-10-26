# Accesser
[中文版本](README.md)

A tool that solves SNI RST, which blocks sites like Wikipedia and Pixiv on the main land of China.

Because the main users of this project are in mainland China, you may encounter a lot of Chinese. Google translate may help you.

[Supported sites](https://github.com/URenko/Accesser/wiki/目前支持的站点)

[![](https://img.shields.io/github/release/URenko/Accesser.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/pypi/v/accesser)](https://pypi.org/project/accesser/)
[![](https://img.shields.io/github/downloads/URenko/Accesser/total.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/license/URenko/Accesser.svg)](https://github.com/URenko/Accesser/blob/master/LICENSE)

## Usage
### If you don't know what Python is
Download Windows executable program from [here](https://github.com/URenko/Accesser/releases/download/v0.10.0/accesser.exe) and run it. The first time you use it, you will be asked to install a certificate, just select yes.
### If Python 3.10* or later is already installed
```
pip3 install -U "accesser[doh,doq]"
```
If you don't need DNS-over-HTTPS and DNS-over-QUIC, you can install without `[doh,doq]`.

Then launch it with the following command:
```
accesser
```
For Windows, by default (without specifying `--notsetproxy`) it will set the system PAC proxy to `http://localhost:7654/pac/?t=<random number>`, if not you can set it manually.

In addition, for Windows, by default (without specifying `--notimportca`) the certificate will be imported to the system automatically, if not you can import it manually, please see [here](https://github.com/URenko/Accesser/wiki/FAQ#q-windows%E8%AE%BF%E9%97%AE%E7%9B%B8%E5%85%B3%E7%BD%91%E7%AB%99%E5%87%BA%E7%8E%B0%E8%AF%81%E4%B9%A6%E9%94%99%E8%AF%AF%E6%82%A8%E7%9A%84%E8%BF%9E%E6%8E%A5%E4%B8%8D%E6%98%AF%E7%A7%81%E5%AF%86%E8%BF%9E%E6%8E%A5neterr_cert_invalid%E4%B9%8B%E7%B1%BB%E7%9A%84%E6%80%8E%E4%B9%88%E5%8A%9E%E8%AF%81%E4%B9%A6%E5%AF%BC%E5%85%A5%E9%94%99%E8%AF%AF%E6%80%8E%E4%B9%88%E5%8A%9E%E5%A6%82%E4%BD%95%E5%8D%B8%E8%BD%BD%E8%AF%81%E4%B9%A6).

*You can use, for example, [pyenv](https://github.com/pyenv/pyenv) to install the required version of Python (Python 3.11+ is recommended).

## Configuration
After starting Accesser once, `config.toml` and `rules.toml` will be generated in the **working directory**. See the comments therein. After saving, reopen the program.

## Advanced Usage 1: Use with other proxy software such as v2ray
Accesser is a local HTTP proxy with a default proxy address of `http://localhost:7654`, which can be used in combination with other proxy software as long as the network traffic can be exported as HTTP proxy.

Take [v2ray](https://github.com/v2fly/v2ray-core) as an example, you can add an HTTP outbound pointing to `http://localhost:7654` and set the corresponding routing rules to send traffic from sites like Wikipedia, Pixiv, etc. to this outbound.
And then run Accesser with the argument `--notsetproxy` to prevent Accesser from setting the system proxy.

In addition, you can set up a DNS outbound and then edit `config.toml` to allow Accesser to use this DNS.

## Advanced Usage 2: Add sites
Edit the pac file in the working directory (if it is a Windows executable program, you can download this file from GitHub to the working directory), so that the websites to be supported can pass through the proxy.

However, not all sites will work straight away and may require some adjustment, see [How to adapt sites](https://github.com/URenko/Accesser/wiki/如何适配站点).