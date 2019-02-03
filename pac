var domains = {
  "steamcommunity.com": 1,
  "pixiv.net": 1,
  "tumblr.com": 1,
  "tumblr.co": 1,
  "google.com": 1,
  "instagram.com": 1,
  "quora.com": 1,
  "reddit.com": 1,
  "redditmedia.com": 1,
  "apkmirror.com": 1
};

var shexps = {
  "*://zh.wikipedia.org/*": 1,
  "*://ja.wikipedia.org/*": 1,
  "*://steamcommunity-a.akamaihd.net/*": 1,
  "*://steamuserimages-a.akamaihd.net/*": 1,
  "*://player.vimeo.com/*": 1,
  "*://*.amazon.co.jp/*": 1,
  "*://onedrive.live.com/*": 1
};

var proxy = "PROXY 127.0.0.1:7655;";

var direct = 'DIRECT;';

var hasOwnProperty = Object.hasOwnProperty;

function shExpMatchs(str, shexps) {
    for (shexp in shexps) {
        if (shExpMatch(str, shexp)) {
            return true;
        }
    }
    return false;
}

function FindProxyForURL(url, host) {
    var suffix;
    var pos = host.lastIndexOf('.');
    pos = host.lastIndexOf('.', pos - 1);
    while(1) {
        if (pos <= 0) {
            if (hasOwnProperty.call(domains, host)) {
                return proxy;
            } else if (shExpMatchs(url, shexps)) {
                return proxy;
            } else {
                return direct;
            }
        }
        suffix = host.substring(pos + 1);
        if (hasOwnProperty.call(domains, suffix)) {
            return proxy;
        }
        pos = host.lastIndexOf('.', pos - 1);
    }
}
