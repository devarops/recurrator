function buildUrlWithParams(baseUrl, path, csvParam) {
    return csvParam
        ? `${baseUrl}${path}?csv=${encodeURIComponent(csvParam)}`
        : `${baseUrl}${path}`;
}

function buildApiUrl(baseUrl, taskId, csvParam) {
    return buildUrlWithParams(baseUrl, `/task/${taskId}`, csvParam);
}

function buildDoneUrl(baseUrl, taskId, csvParam) {
    return buildUrlWithParams(baseUrl, `/task/${taskId}/done`, csvParam);
}

function renderTask(task) {
    return `
        <table>
            <tbody>
                <tr><td>ID</td><td>${task.id}</td></tr>
                <tr><td>Description</td><td>${task.description}</td></tr>
                <tr><td>Context</td><td>${task.context}</td></tr>
                <tr><td>Skip Count</td><td>${task.skip_count}</td></tr>
                <tr><td>Starred</td><td>${task.starred ? 'Yes' : 'No'}</td></tr>
                <tr><td>Latest Date</td><td>${task.latest_date}</td></tr>
                <tr><td>Recurrence</td><td>${task.recurrence_days} days</td></tr>
                <tr><td>Due Date</td><td>${task.due_date}</td></tr>
            </tbody>
        </table>
        <button id="doneBtn">Mark as Done</button>
    `;
}

function renderError(error) {
    return `Error: ${error.message}`;
}

function fetchJson(url, options = {}) {
    return fetch(url, options).then(r => r.json());
}

function getQueryParams() {
    return {
        taskId: new URL(window.location).searchParams.get('id'),
        csvParam: new URL(window.location).searchParams.get('csv')
    };
}

function getDomElements() {
    return {
        taskElement: document.getElementById('task'),
        errorElement: document.getElementById('error')
    };
}

function displayTask(taskElement, errorElement, task) {
    taskElement.innerHTML = renderTask(task);
    errorElement.hidden = true;
}

function displayError(errorElement, error) {
    errorElement.innerHTML = renderError(error);
    errorElement.hidden = false;
}

function attachDoneButtonHandler(doneBtn, context) {
    const { apiBaseUrl, taskId, csvParam, taskElement, errorElement, apiUrl } = context;

    doneBtn.addEventListener('click', () => {
        const doneUrl = buildDoneUrl(apiBaseUrl, taskId, csvParam);
        fetchJson(doneUrl, { method: 'POST' })
            .then(() => fetchJson(apiUrl))
            .then(updatedTask => {
                displayTask(taskElement, errorElement, updatedTask);
                const newDoneBtn = document.getElementById('doneBtn');
                attachDoneButtonHandler(newDoneBtn, context);
            })
            .catch(err => {
                displayError(errorElement, err);
            });
    });
}

function init(apiBaseUrl) {
    const { taskElement, errorElement } = getDomElements();
    const { taskId, csvParam } = getQueryParams();
    const apiUrl = buildApiUrl(apiBaseUrl, taskId, csvParam);

    fetchJson(apiUrl)
        .then(task => {
            displayTask(taskElement, errorElement, task);
            const doneBtn = document.getElementById('doneBtn');
            const context = { apiBaseUrl, taskId, csvParam, taskElement, errorElement, apiUrl };
            attachDoneButtonHandler(doneBtn, context);
        })
        .catch(err => {
            displayError(errorElement, err);
        });
}

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    init('http://localhost:8000');
});
