# SentinelHub

An OSWE-style white-box lab. A Flask alerting platform with a few real
weaknesses buried in otherwise normal business logic.

Most open-source lab targets put the vulnerability right in your face — you see
the endpoint and you already know the answer, which teaches you nothing about
source review. This one goes the other way: the bugs are hidden in normal code,
and no single bug gets you to code execution. You register an account, then
follow the business logic until something finally lets you run commands.

> For authorized lab use only. Don't expose it to the internet.

## Run

```bash
pip install -r requirements.txt
python wsgi.py
# or: docker-compose up --build
```

Default at http://localhost:5000. Seeded accounts: `admin/admin123`,
`demo/demo123`. Registration is open.

## Misc

- 19 blueprints, 69 routes, ~3400 lines of Python. Monitoring, billing,
  notifications, reports — the usual product surface.
- After a successful exploit, `cat /flag.txt` in the container.
- `exp/` has the exploit scripts for the three chains.
- Why it's built this way: [DESIGN.md](DESIGN.md).

## License

MIT
