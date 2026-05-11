function getTodayISO() {
    return new Date().toISOString().split('T')[0];
}

function getQueryParams() {
    return {
        csvParam: new URL(window.location).searchParams.get('csv')
    };
}

function buildContextUrl(baseUrl, csvParam) {
    const today = getTodayISO();
    const url = `${baseUrl}/context/?date=${today}`;
    return csvParam
        ? `${url}&csv=${encodeURIComponent(csvParam)}`
        : url;
}

function renderContextList(contexts) {
    if (contexts.length === 0) {
        return '<p>No tasks due.</p>';
    }

    const { csvParam } = getQueryParams();
    const items = contexts.map(ctx => {
        const href = csvParam
            ? `context.html?context=${encodeURIComponent(ctx)}&csv=${encodeURIComponent(csvParam)}`
            : `context.html?context=${encodeURIComponent(ctx)}`;
        return `<li><a href="${href}">${ctx}</a></li>`;
    }).join('');

    return `<ul>${items}</ul>`;
}

function init(apiBaseUrl) {
    const contextsElement = document.getElementById('contexts');
    const errorElement = document.getElementById('error');
    const { csvParam } = getQueryParams();
    const url = buildContextUrl(apiBaseUrl, csvParam);

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(contexts => {
            contextsElement.innerHTML = renderContextList(contexts);
        })
        .catch(err => {
            errorElement.innerHTML = `Error: ${err.message}`;
            errorElement.hidden = false;
            contextsElement.innerHTML = '';
        });
}

document.addEventListener('DOMContentLoaded', () => {
    init('http://localhost:8000');
});
