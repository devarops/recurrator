const API_BASE_URL = 'http://localhost:8000';

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

function initTaskPage(apiBaseUrl) {
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

function getTodayISO() {
    return new Date().toISOString().split('T')[0];
}

function buildContextUrl(baseUrl, csvParam) {
    const today = getTodayISO();
    const url = `${baseUrl}/context/?date=${today}`;
    return csvParam
        ? `${url}&csv=${encodeURIComponent(csvParam)}`
        : url;
}

function renderContextList(contexts, csvParam) {
    if (contexts.length === 0) {
        return '<p>No tasks due.</p>';
    }

    const items = contexts.map(ctx => {
        const href = csvParam
            ? `context.html?context=${encodeURIComponent(ctx)}&csv=${encodeURIComponent(csvParam)}`
            : `context.html?context=${encodeURIComponent(ctx)}`;
        return `<li><a href="${href}">${ctx}</a></li>`;
    }).join('');

    return `<ul>${items}</ul>`;
}

function buildTasksByContextUrl(baseUrl, contextName, csvParam) {
    const today = getTodayISO();
    const url = `${baseUrl}/context/${encodeURIComponent(contextName)}?date=${today}`;
    return csvParam
        ? `${url}&csv=${encodeURIComponent(csvParam)}`
        : url;
}

function renderTaskLinks(taskIds, csvParam) {
    if (taskIds.length === 0) {
        return '<p>No tasks due.</p>';
    }

    const items = taskIds.map(id => {
        const href = csvParam
            ? `task.html?id=${id}&csv=${encodeURIComponent(csvParam)}`
            : `task.html?id=${id}`;
        return `<li><a href="${href}">Task ${id}</a></li>`;
    }).join('');

    return `<ul>${items}</ul>`;
}

function initContextPage(apiBaseUrl) {
    const tasksElement = document.getElementById('tasks');
    const errorElement = document.getElementById('error');
    const contextNameElement = document.getElementById('contextName');
    const params = new URL(window.location).searchParams;
    const contextName = params.get('context');
    const csvParam = params.get('csv');

    if (contextName) {
        contextNameElement.textContent = `Context: ${contextName}`;
    }

    const url = buildTasksByContextUrl(apiBaseUrl, contextName, csvParam);

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(taskIds => {
            tasksElement.innerHTML = renderTaskLinks(taskIds, csvParam);
        })
        .catch(err => {
            displayError(errorElement, err);
            tasksElement.innerHTML = '';
        });
}

function initIndexPage(apiBaseUrl) {
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
            contextsElement.innerHTML = renderContextList(contexts, csvParam);
        })
        .catch(err => {
            displayError(errorElement, err);
            contextsElement.innerHTML = '';
        });
}

function initPage() {
    const contextsElement = document.getElementById('contexts');
    const tasksElement = document.getElementById('tasks');
    if (contextsElement) {
        initIndexPage(API_BASE_URL);
        return;
    }
    if (tasksElement) {
        initContextPage(API_BASE_URL);
        return;
    }
    initTaskPage(API_BASE_URL);
}

document.addEventListener('DOMContentLoaded', () => {
    initPage();
});
