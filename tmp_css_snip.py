from pathlib import Path
path=Path('shopur/users/static/css/style.css')
print(path.read_text('utf-8')[:400])
