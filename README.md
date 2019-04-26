## 支持的站点
理论上支持绝大部分被DNS污染和SNI RST的站点。你可以[在这里](https://github.com/URenko/Accesser/wiki/目前支持的站点)找到目前默认支持的站点，但是您可以通过配置自行增加站点。

## 使用教程

### Windows 64位
从页面上方按钮下载，运行既可，首次使用会要求安装证书（如下图），选**是**即可。需要关闭时点击[网页](http://localhost:7654)上的**关闭**既可。

![](https://i.loli.net/2019/02/04/5c57f7cf655fd.png)

### Windows 32位和XP
32位系统由于使用量较少，暂不提供一键使用程序，可参考下文Linux和macOS进行配置，或者考虑升级为64位系统。由于Python 3.5起Windows XP已不受支持，故我们也不支持Windows XP，请升级您的系统。

### Linux和macOS
我们暂时未提供一键使用程序，可按如下步骤操作：

1. 从页面上方按钮下载源码，并解压
2. 下载**Python3.7**，我们推荐从[Python官网](https://www.python.org/downloads/release/python-373/)下载。此外，在Linux下，我们推荐使用[pyenv](https://github.com/pyenv/pyenv-installer)来管理不同版本的Python
3. 安装依赖包：
```
pip3 install pyopenssl doh-proxy tld tornado
pip3 install -U git+https://github.com/URenko/aioh2.git
```
4. 设置PAC代理为`http://127.0.0.1:7654/pac/`
5. 运行程序：`python3 accesser.py`
6. 点击导入证书来下载证书，然后手动导入证书
7. 对于Firefox浏览器，还需按照[https://github.com/URenko/Accesser/wiki/Firefox设置方法](https://github.com/URenko/Accesser/wiki/Firefox设置方法)进行设置

## 有问题？

如果您在使用过程中遇到了问题，请阅读[FAQ](https://github.com/URenko/Accesser/wiki/FAQ)，或者[发issue](https://github.com/URenko/Accesser/issues)求助，或者在Telegram上联系[@URenko](https://t.me/URenko)

如果您启动了程序，请在描述问题时附上日志。对于一键程序，同目录下的`accesser.log`就是日志文件。