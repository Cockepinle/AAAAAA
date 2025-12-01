import pathlib
from pathlib import Path
text=Path('shopur/users/static/css/style.css').read_text('utf-8')
start=text.index('.order-info-grid .info-card')
print(text[start:start+200])
