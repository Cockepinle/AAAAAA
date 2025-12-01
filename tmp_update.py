import pathlib
path=pathlib.Path('shopur/users/static/css/style.css')
text=path.read_text('utf-8')
old=""".order-detail-page{\r\n    background:var(--bg);\r\n}"""
new=""".order-detail-page{\r\n    background:linear-gradient(180deg,rgba(248,245,239,.7) 0,rgba(248,245,239,1) 40%);\r\n}\r\n.order-detail-page .container{\r\n    max-width:1100px;\r\n    margin:0 auto;\r\n}"""
if old not in text:
    raise SystemExit('order-detail block not found')
text=text.replace(old,new,1)
path.write_text(text,'utf-8')
