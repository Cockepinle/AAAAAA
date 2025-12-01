import pathlib
path=pathlib.Path('shopur/users/static/css/style.css')
text=path.read_text('utf-8')
start=text.find('.order-detail-page')
print(repr(text[start:start+120]))
