# SentinelHub

练 OSWE 用的白盒靶场。一个 Flask 写的告警平台,把几个真实弱点藏在正常业务逻辑里。

大多数开源靶场的洞都摆在明面上,看到接口就等于知道答案,练不到审计。这个反过来:洞埋在一堆正常代码里,单个洞到不了远程代码执行,得先搞个账号,再顺着业务链一路摸到底。

> 仅供授权靶场使用,别暴露到公网。

## 跑起来

```bash
pip install -r requirements.txt
python wsgi.py
# 或者 docker-compose up --build
```

默认地址 http://localhost:5000,内置 `admin/admin123`、`demo/demo123`,也开放注册。

## 别的

- 19 个 blueprint、69 条路由、3400 行 Python,监控、计费、通知、报告那一套业务都有。
- 打穿后容器里 `cat /flag.txt`。
- `exp/` 是三条链的利用脚本。

## License

MIT
