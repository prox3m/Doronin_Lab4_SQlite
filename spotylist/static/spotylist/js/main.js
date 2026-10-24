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

saveButton.addEventListener('click', function() {
    const formData = new FormData();
    formData.append('name', albumName.value);
    formData.append('authors', albumAuthors.value);
    formData.append('length', ablumLength.value);

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

    fetch('/create/', {method: 'POST', body: formData,}).then(() => {window.location.reload();});
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

    fetch('/import/', {method: 'POST', body: formData,}).then(() => {window.location.reload();});
});