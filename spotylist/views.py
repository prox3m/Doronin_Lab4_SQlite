from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from .models import Album, Track
from django.db.models import Q
from pathlib import Path
import json, re, time

DATA_FILE = Path(settings.BASE_DIR) / 'data' / 'albums.json'
TIME_RE = re.compile(r'^(\d+:)?\d{1,2}:\d{1,2}:\d{1,2}$')
MEDIA_COVERS = Path(settings.MEDIA_ROOT) / 'covers'

def index(request):
    source = request.GET.get('source', 'file')

    if source == 'db':
        db_albums = Album.objects.all().prefetch_related('tracks').order_by('-created_at')

        albums = []

        for album in db_albums:
            albums.append({
                'name': album.name,
                'authors': album.authors,
                'length': album.length,
                'price': album.price,
                'country': album.country,
                'image': album.image,
                'image_url': f'/media/{album.image}' if album.image else '/static/spotylist/images/undefined.jpeg',
                'tracks': [track.name for track in album.tracks.all()],
                'is_db': True,
                'id': album.id
            })
    else:
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

    save_destination = request.POST.get('save_destination', 'file')

    album_data = {
        'name': request.POST.get('name', '').strip(),
        'image': '',
        'authors': request.POST.get('authors', '').strip(),
        'length': request.POST.get('length', '').strip(),
        'price': request.POST.get('price', '').strip(),
        'country': request.POST.get('country', '').strip(),
        'tracks': request.POST.getlist('tracks'),
    }

    errors = validate(album_data)
    if errors:
        for error in errors:
            messages.error(request, error)
        return redirect('index')

    image_path = ''
    if 'image' in request.FILES:
        file = request.FILES['image']
        file_name = f'{int(time.time())}_{file.name}'
        MEDIA_COVERS.mkdir(parents=True, exist_ok=True)
        full_path = MEDIA_COVERS / file_name

        with open(full_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        
        image_path = f'covers/{file_name}'
    
    album_data['image'] = image_path

    if save_destination == 'db':
        if Album.objects.filter(name=album_data['name'], authors=album_data['authors']).exists():
            messages.error(request, 'Такой альбом уже существует в базе данных')
            return redirect('index.html')

        new_ablum = Album.objects.create(
            name = album_data['name'],
            authors = album_data['authors'],
            length = album_data['length'],
            price = album_data['price'] if album_data['price'] else None,
            country = album_data['country'],
            image = album_data['image']
        )

        for i, track_name in enumerate(album_data['tracks']):
            Track.objects.create(album=new_ablum, name=track_name, order=i)

        messages.success(request, f'Альбом ◄{album_data["name"]}► сохранен в базу данных')
    else:
        albums = read_albums()
        album_data['index'] = max((a.get('index', -1) for a in albums), default=-1) + 1
        albums.append(album_data)
        write_albums(albums)
        
        messages.success(request, f'Альбом ◄{album_data["name"]}► сохранен в файл')

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

def search_albums(request):
    query = request.GET.get('q', '').strip()
    source = request.GET.get('source', 'file')

    if source == 'db':
        db_albums = Album.objects.filter(
            Q(name__icontains=query) |
            Q(authors__icontains=query) |
            Q(tracks__name__icontains=query)
        ).distinct().prefetch_related('tracks')

        albums = []
        for album in db_albums:
            albums.append({
                'name': album.name,
                'authors': album.authors,
                'length': album.length,
                'price': album.price,
                'country': album.country,
                'image': album.image,
                'image_url': f'/media/{album.image}' if album.image else '/static/spotylist/images/undefined.jpeg',
                'tracks': [track.name for track in album.tracks.all()],
                'is_db': True,
                'id': album.id
            })
    else:
        all_albums = read_albums()
        albums = []

        for album in all_albums:
            name = album.get('name', '') or ''
            authors = album.get('authors', '') or ''
            tracks = album.get('tracks') or []


            if (query.lower() in name.lower() or
               query.lower() in authors.lower() or
               any(query.lower() in str(track).lower() for track in tracks)):

                if album.get('image'):
                    album['image_url'] = f'/media/{album["image"]}'
                else:
                    album['image_url'] = '/static/spotylist/images/undefined.jpeg'

                album['is_db'] = False
                albums.append(album)

    html = render_to_string('spotylist/_album_cards.html', {'albums': albums})
    return HttpResponse(html)

def delete_album(request):
    if request.method == 'POST':
        album_id = request.POST.get('id')
        
        try:
            album = Album.objects.get(id = album_id)
            album.delete()
            return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')
        except Album.DoesNotExist:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Не наиден'}), content_type='application/json')

    return HttpResponse(json.dumps({'status': 'error'}), content_type='application/json')

def edit_album(request):
    if request.method == 'POST':
        album_id = request.POST.get('id')

        album_data = {
            'name': request.POST.get('name', '').strip(),
            'authors': request.POST.get('authors', '').strip(),
            'length': request.POST.get('length', '').strip(),
            'price': request.POST.get('price', '').strip(),
            'country': request.POST.get('country', '').strip(),
            'tracks': [track.strip() for track in request.POST.get('tracks', '').split(';') if track.strip()]
        }

        errors = validate(album_data)
        if errors:
            return HttpResponse(json.dumps({'status':'error', 'message': '; '.join(errors)}), content_type='application/json')

        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Альбом не надиен'}), content_type='application/json')

        if Album.objects.filter(name=album_data['name'], authors=album_data['authors']).exclude(id=album_id).exists():
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Альбом с таким названием и автором существует'}), content_type='application/json')

        album.name = album_data['name']
        album.authors = album_data['authors']
        album.length = album_data['length']
        album.price = album_data['price'] if album_data['price'] else None
        album.country = album_data['country']

        album.save()

        album.tracks.all().delete()

        for i, track_name in enumerate(album_data['tracks']):
            Track.objects.create(album=album, name=track_name, order=i)

        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')