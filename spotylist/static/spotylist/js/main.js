const trackInput = document.getElementById('track-input');
const addButton = document.getElementById('add-track-btn');
const trackList = document.getElementById('track-list-edit');

addButton.addEventListener('click', function () {
    const trackName = trackInput.value.trim();

    if (!trackName) {
        return;
    }

    const row = document.createElement('div');
    row.className = 'track-edit-row';

    const name = document.createElement('span');
    name.className = 'track-edit-name';
    name.textContent = trackName;

    const button = document.createElement('button');
    button.className = 'remove-track';
    button.textContent = 'X';
    button.addEventListener('click', function() {
        row.remove();
    });

    row.appendChild(name);
    row.appendChild(button);

    trackList.appendChild(row);
    trackInput.value = '';
});


const saveButton = document.getElementById('save-btn');
const albumName = document.getElementById('album-name');
const albumAuthors = document.getElementById('album-authors');
const ablumLength = document.getElementById('album-length');
const albumPrice = document.getElementById('album-price');
const albumCountry = document.getElementById('album-country');

saveButton.addEventListener('click', function() {
    const formData = new FormData();

    const saveDestination = document.querySelector('input[name="save_destination"]:checked').value;
    formData.append('save_destination', saveDestination);
    
    formData.append('name', albumName.value);
    formData.append('authors', albumAuthors.value);
    formData.append('length', ablumLength.value);
    formData.append('price', albumPrice.value);
    formData.append('country', albumCountry.value);

    const imageFile = fileInput.files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    formData.append('csrfmiddlewaretoken', csrfToken);

    const tracksRow = document.querySelectorAll('.track-edit-row');
    tracksRow.forEach( row => {
        const name = row.querySelector('.track-edit-name').textContent;
        formData.append('tracks', name);
    })

    fetch('/create/', {method: 'POST', body: formData, redirect: 'manual',}).then(() => {window.location.reload();});
});


const fileInput = document.getElementById('album-image');
const fileName = document.getElementById('file-name');

fileInput.addEventListener('change', function() {
    if (fileInput.isDefaultNamespace.length > 0) {
        fileName.textContent = fileInput.files[0].name;
    } else {
        fileName.textContent = 'Файл не выбран';
    }
});


const importButton = document.getElementById('import-btn');
const importInput = document.getElementById('import-input');

importButton.addEventListener('click', function() {
    importInput.click();
});

importInput.addEventListener('change', function() {
    const file = importInput.files[0];
    if (!file) {
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch('/import/', {method: 'POST', body: formData, redirect: 'manual',}).then(() => {importInput.value = ''; window.location.reload();});
});


const searchInput = document.getElementById('search-input');
const albumsGrid = document.querySelector('.albums-grid');

const urlParams = new URLSearchParams(window.location.search);
const currentSource = urlParams.get('source') || 'file';

searchInput.addEventListener('input', function() {
    const query = searchInput.value;

    fetch(`/search/?q=${encodeURIComponent(query)}&source=${currentSource}`)
        .then(response => response.text())
        .then(html => {
            albumsGrid.innerHTML = html;
        });
});

albumsGrid.addEventListener('click', function(event) {
    if (event.target.classList.contains('delete-btn')) {
        const albumId = event.target.getAttribute('data-id');
        const card = event.target.closest('.album-card');

        if (confirm('Вы уверены, что хотите удалить альбом?')) {
            const formData = new FormData();
            formData.append('id', albumId);

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            formData.append('csrfmiddlewaretoken', csrfToken);

            fetch('/delete/', {
                method: 'POST',
                body: formData
            }).then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    card.remove();
                } else {
                    alert('Ошибка при удалении');
                }
            });
        }
    }
});

const editModal = new bootstrap.Modal(document.getElementById('editModal'));
const editForm = document.getElementById('edit-form');

albumsGrid.addEventListener('click', function(event) {
    if (event.target.classList.contains('edit-btn')) {
        document.getElementById('edit-id').value = event.target.getAttribute('data-id');
        document.getElementById('edit-name').value = event.target.getAttribute('data-name');
        document.getElementById('edit-authors').value = event.target.getAttribute('data-authors');
        document.getElementById('edit-length').value = event.target.getAttribute('data-length');
        document.getElementById('edit-price').value = event.target.getAttribute('data-price');
        document.getElementById('edit-country').value = event.target.getAttribute('data-country');
        document.getElementById('edit-tracks').value = event.target.getAttribute('data-tracks');

        document.getElementById('edit-error').innerText = '';
        editModal.show();
    }
});

editForm.addEventListener('submit', function(event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append('id', document.getElementById('edit-id').value);
    formData.append('name', document.getElementById('edit-name').value);
    formData.append('authors', document.getElementById('edit-authors').value);
    formData.append('length', document.getElementById('edit-length').value);
    formData.append('price', document.getElementById('edit-price').value);
    formData.append('country', document.getElementById('edit-country').value);
    formData.append('tracks', document.getElementById('edit-tracks').value);

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch('/edit/', {method: 'POST', body: formData})
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            window.location.reload();
        } else {
            document.getElementById('edit-error').innerText = data.message;
        }
    });
});