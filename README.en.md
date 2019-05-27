# Accesser
[中文版本](README.md)

A tool that solves SNI RST, which blocks sites like Wikipedia and Pixiv on the main land of China.

Because the main users of this project are in mainland China, you may encounter a lot of Chinese. Google translate may help you.

[Supported sites](https://github.com/URenko/Accesser/wiki/目前支持的站点)

[![](https://img.shields.io/github/release/URenko/Accesser.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/downloads/URenko/Accesser/total.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/license/URenko/Accesser.svg)](https://github.com/URenko/Accesser/blob/master/LICENSE)

## Usage
refer to [https://urenko.github.io/Accesser/](https://urenko.github.io/Accesser/)

## Requirements
- Python3.7 (Other versions not tested)
- [pyopenssl](https://pyopenssl.org/)
- [sysproxy](https://github.com/Noisyfox/sysproxy)(for Windows)
- dnspython
- [dnscrypt-proxy](https://github.com/jedisct1/dnscrypt-proxy)
- tornado
- tld

## Add sites
Follow [Developer's Guide](https://github.com/URenko/Accesser/wiki/开发者指南) to configure the environment, then edit the `template/pac` with pac file format to make traffic through the proxy.

## Current support
|                                            |Windows|Mac OS|Linux|
|--------------------------------------------|-------|------|-----|
|Basic support                               |  ✔  |  ✔  | ✔ |
|Automatically configure the pac agent       |  ✔  |      |     |
|Automatically import certificates to system |  ✔  |      |     |
