console.log("common.js")
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