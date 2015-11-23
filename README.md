##Reloader

* 这是搞毛的呢? 其实就是自动重载服务, 曾经使用比较挫的 `nginx -s reload`, 现在改用 openresty 了.
* openresty 的代码和镜像参考[这里](https://github.com/HunanTV/eru-lb)

##Run

### Install
* `pip install eru-reloader --upgrade`
* `git clone` and `python setup.py install`

### Config
* `eru-reloader --help` 会告诉你哪些需要配置.
* 使用 openresty 作为 reloader 需要配置 ainur 一起用.