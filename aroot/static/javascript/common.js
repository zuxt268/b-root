
function post(path, dict) {
    let form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', path);
    Object.entries(dict).forEach(([key, value]) => {
        let field = document.createElement('input');
        field.setAttribute('type', 'hidden');
        field.setAttribute('name', key);
        field.setAttribute('value', String(value));
        form.appendChild(field);
    });
    document.body.appendChild(form);
    form.submit();
}

// オーバーレイを表示する関数
function showLoadingOverlay() {
    document.getElementById('loading-overlay').classList.remove('d-none');
    document.getElementById('loading-overlay').classList.add('d-flex');
}

// オーバーレイを非表示にする関数
function hideLoadingOverlay() {
    document.getElementById('loading-overlay').classList.add('d-none');
    document.getElementById('loading-overlay').classList.remove('d-flex');
}

window.addEventListener('pageshow', function (event) {
    if (event.persisted) { // Checks if the page was loaded from cache
        hideLoadingOverlay(); // Your function to hide the loading overlay
    }
});