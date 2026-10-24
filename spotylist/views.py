from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from pathlib import Path
import json, re

DATA_FILE = Path(settings.BASE_DIR) / 'data' / 'albums.json'
TIME_RE = re.compile(r'^(\d+:)?\d{1,2}:\d{1,2}:\d{1,2}$')
MEDIA_COVERS = Path(settings.MEDIA_ROOT) / 'covers'

def index(request):
    albums = read_albums()

    for album in albums:
        if album.get('image'):
            album['image_url'] = f'/media/{album["image"]}'
        else:
            album['image_url'] = '/static/spotylist/images/undefined.jpeg'

    return render(request, 'spotylist/index.html', {'albums': albums})

def read_albums():
    if not DATA_FILE.exists():
        return []

    file_text = DATA_FILE.read_text(encoding='utf-8').strip()
    if not file_text:
        return []

    try:
        return json.loads(file_text)
    except json.JSONDecodeError:
        return []

def create_album(request):
    if request.method != 'POST':
        return redirect('index')

    album_data = {
        'name': request.POST.get('name', '').strip(),
        'image': '',
        'authors': request.POST.get('authors', '').strip(),
        'length': request.POST.get('length', '').strip(),
        'price': request.POST.get('price', '').strip(),
        'tracks': request.POST.getlist('tracks'),
    }

    errors = validate(album_data)
    if errors:
        for error in errors:
            messages.error(request, error)
        return redirect('index')
    
    albums = read_albums()
    album_data['index'] = max((a.get('index', -1) for a in albums), default=-1) + 1

    image_path = ''
    if 'image' in request.FILES:
        file = request.FILES['image']
        file_name = f'{album_data["index"]}_{file.name}'
        MEDIA_COVERS.mkdir(parents=True, exist_ok=True)
        full_path = MEDIA_COVERS / file_name

        with open(full_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        
        image_path = f'covers/{file_name}'
    
    album_data['image'] = image_path

    albums.append(album_data)
    write_albums(albums)

    messages.success(request, f'Альбом ◄{album_data["name"]}► сохранен!')
    return redirect('index')

def validate(album):
    not_valid = []

    name = album.get('name', '')
    if name.strip() == '':
        not_valid.append('Название обязательно')

    price = album.get('price', '')
    if price:
        if not price.isdigit():
            try:
                float(price)
            except ValueError:
                not_valid.append('Стоимость не числовая')
    
    length = album.get('length', '')
    if not TIME_RE.match(length.strip()):
        not_valid.append('Неверный формат времени')
    
    tracks = album.get('tracks', [])

    if type(tracks) is list:
        for i, track in enumerate(tracks):
            if not track.strip():
                not_valid.append(f"Пустой трек №{i + 1} в списке")
    else:
        not_valid.append("Треки должны быть списком")
    
    return not_valid

def write_albums(albums):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    text = json.dumps(albums, ensure_ascii=False, indent=4)
    DATA_FILE.write_text(text, encoding="utf-8")

def import_album(request):
    if request.method != 'POST':
        return redirect('index')
    
    file = request.FILES.get('file')
    if not file:
        messages.error(request, "Не удалось получить файл")
        return redirect('index')

    if not file.name.lower().endswith('.json'):
        messages.error(request, "Файл должен быть в формате .json")
        return redirect('index')

    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        messages.error(request, 'Файл не является корректным JSON')
        return redirect('index')

    if isinstance(data, dict):
        albums_to_import = [data]
    elif isinstance(data, list):
        albums_to_import = data
    else:
        messages.error(request, 'JSON должен быть объектом или списком объектов')
        return redirect('index')

    albums = read_albums()
    
    for i, album in enumerate(albums_to_import):
        if not isinstance(album, dict):
            messages.error(request, f'Альбом №{i + 1} не является объектом')
            return redirect('index')

        errors = validate(album)
        if errors:
            for error in errors:
                messages.error(request, f'Альбом №{i + 1}: {error}')
            return redirect('index')

    for album in albums_to_import:
        album.setdefault('authors', '')
        album.setdefault('length', '')
        album.setdefault('price', '')
        album.setdefault('image', '')
        album.setdefault('tracks', [])

        album['index'] = max((a.get('index', -1) for a in albums), default=-1) + 1
        albums.append(album)

    write_albums(albums)
    messages.success(request, f'Импортировано альбомов: {len(albums_to_import)}')
    return redirect('index')