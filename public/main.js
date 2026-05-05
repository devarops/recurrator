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

function renderTaskRow(label, value) {
    return `<tr><td>${label}</td><td>${value}</td></tr>`;
}

function renderTask(task) {
    return `
        <table>
            <tbody>
                ${renderTaskRow('ID', task.id)}
                ${renderTaskRow('Description', task.description)}
                ${renderTaskRow('Context', task.context)}
                ${renderTaskRow('Skip Count', task.skip_count)}
                ${renderTaskRow('Starred', task.starred ? 'Yes' : 'No')}
                ${renderTaskRow('Latest Date', task.latest_date)}
                ${renderTaskRow('Recurrence', `${task.recurrence_days} days`)}
                ${renderTaskRow('Due Date', task.due_date)}
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

function markDoneAndRefresh(context) {
    const { apiBaseUrl, taskId, csvParam, taskElement, errorElement, apiUrl } = context;
    const doneUrl = buildDoneUrl(apiBaseUrl, taskId, csvParam);

    return fetchJson(doneUrl, { method: 'POST' })
        .then(() => fetchJson(apiUrl))
        .then(updatedTask => {
            displayTask(taskElement, errorElement, updatedTask);
            return updatedTask;
        })
        .catch(err => {
            displayError(errorElement, err);
            throw err;
        });
}

function attachDoneButtonHandler(doneBtn, context) {
    doneBtn.addEventListener('click', () => {
        markDoneAndRefresh(context)
            .then(() => {
                const newDoneBtn = document.getElementById('doneBtn');
                attachDoneButtonHandler(newDoneBtn, context);
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
