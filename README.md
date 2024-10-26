# Accesser
[English version](README.en.md)

一个解决SNI RST导致维基百科、Pixiv等站点无法访问的工具  
[支持的站点](https://github.com/URenko/Accesser/wiki/目前支持的站点)

[![](https://img.shields.io/github/release/URenko/Accesser.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/pypi/v/accesser)](https://pypi.org/project/accesser/)
[![](https://img.shields.io/github/downloads/URenko/Accesser/total.svg)](https://github.com/URenko/Accesser/releases/latest)
[![](https://img.shields.io/github/license/URenko/Accesser.svg)](https://github.com/URenko/Accesser/blob/master/LICENSE)

## 使用
### 如果不知道什么是Python
从[这里](https://github.com/URenko/Accesser/releases/download/v0.10.0/accesser.exe)下载Windows一键程序，运行既可（建议关闭其他代理软件），首次使用会要求安装证书，选是即可。
### 如果已经安装了Python 3.10*或更高版本
```
pip3 install -U "accesser[doh,doq]"
```
如果你不需要 DNS-over-HTTPS 和 DNS-over-QUIC，则可以不用带`[doh,doq]`。

然后通过如下命令启动：
```
accesser
```
对于Windows系统，默认情况下（没有指定`--notsetproxy`）会设置PAC代理为`http://localhost:7654/pac/?t=<随机数>`，如果没有可以手动设置。

此外，对于Windows系统，默认情况下（没有指定`--notimportca`）会自动导入证书至系统，如果没有可以手动导入，请看[这里](https://github.com/URenko/Accesser/wiki/FAQ#q-windows%E8%AE%BF%E9%97%AE%E7%9B%B8%E5%85%B3%E7%BD%91%E7%AB%99%E5%87%BA%E7%8E%B0%E8%AF%81%E4%B9%A6%E9%94%99%E8%AF%AF%E6%82%A8%E7%9A%84%E8%BF%9E%E6%8E%A5%E4%B8%8D%E6%98%AF%E7%A7%81%E5%AF%86%E8%BF%9E%E6%8E%A5neterr_cert_invalid%E4%B9%8B%E7%B1%BB%E7%9A%84%E6%80%8E%E4%B9%88%E5%8A%9E%E8%AF%81%E4%B9%A6%E5%AF%BC%E5%85%A5%E9%94%99%E8%AF%AF%E6%80%8E%E4%B9%88%E5%8A%9E%E5%A6%82%E4%BD%95%E5%8D%B8%E8%BD%BD%E8%AF%81%E4%B9%A6)。

*可以使用例如[pyenv](https://github.com/pyenv/pyenv)来安装所需的Python版本（推荐Python 3.11+）。

## 设置
启动一次Accesser后，会在 **工作目录** 下生成`config.toml` 和 `rules.toml`，具体含义见其中注释，保存后重新打开程序。

## 进阶1: 与v2ray等其他代理软件一起使用
Accesser是一个本地HTTP代理，默认代理地址为`http://localhost:7654`，只要网络流量能从其他代理软件以HTTP代理导出就能联合使用。

以[v2ray](https://github.com/v2fly/v2ray-core)为例，可以添加一个HTTP的outbound指向`http://localhost:7654`，并设置相应的路由规则，将维基百科、Pixiv等站点的流量送到这个outbound。
并在启动 Accesser 时带上 `--notsetproxy` 参数以避免 Accesser 设置系统代理。

此外，你还可以设置一个DNS outbound，然后编辑`config.toml`让Accesser使用这一DNS。

## 进阶2: 增加支持的网站
编辑工作目录下的pac文件（如果是一键程序，可以从GitHub下载这一文件到工作目录），使要支持的网站从代理过。

然而，并不是所有站点都可以直接工作，可能需要一些调节，见[如何适配站点](https://github.com/URenko/Accesser/wiki/如何适配站点)。

---

<details>

<summary>时间线与后记</summary>
  
18年夏，通过修改 hosts 以连接被 GFW 屏蔽的维基百科、pixiv 等网站的方法突然失效。很快人们就[反应过来](https://github.com/googlehosts/hosts/issues/87)问题的所在：SNI RST。
在这之前，修改 hosts 是一个几近于零成本的翻墙方法。突然的变化意味着翻墙成本的急剧上升。

为了重置平衡，同时抱着对更早时期红杏计划的敬佩，我翻阅了关于 TLS 的 RFC 文档，并注意到其中关于 SNI RST 涉及的 `server_name` 并非 "must"，而是可选扩展。
经过[简单测试](https://github.com/URenko/Access_demo)，确认这一思路确实可行。
秉着重置平衡的想法，我制作了 Accesser，并配备了 web UI （现已移除），目的就是让一般人访问维基百科、pixiv 等网站的难度降低到 hosts 时代的水平。
尽管我仅在一个极小众论坛（现已关闭）上自荐过，一段时间后，Accesser 甚至成了中文维基社群推荐的方法。

在这之后，利用相同思路的翻墙软件/方法如春笋般涌现。不过稍微遗憾的是，他们中的许多没有做和远程服务器之间的证书校验，使得用户暴露在可能的危险中。
再往后，一些更加投机取巧，利用非标准协议的方法也有出现。

19年后，因日渐繁忙，加之坚信这一如此简单的思路很快就会失效，故停更。

22年末，契机是 Python 的协程接口日渐稳定，并出现[需要的功能](https://docs.python.org/zh-cn/3/whatsnew/3.11.html#asyncio)，我将 Accesser 的核心重写并在各位贡献者的协助下陆续更新。

Accesser 的大版本号是留予新的技术，然而出乎我的预料，现有的域前置技术在六年后仍未失效。
而另一方面，看起来天朝人民有足够的能力以维持平衡，因此 1.x 可能永远不会到来。
</details>
