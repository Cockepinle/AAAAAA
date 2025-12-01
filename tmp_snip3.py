import pathlib
text=pathlib.Path('shopur/users/static/css/style.css').read_text('utf-8')
start=text.find('.order-items-table')
print(text[start:start+200])
