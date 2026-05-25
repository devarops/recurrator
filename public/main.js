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

function _fetchAndRender(url, renderFn, contentElement, errorElement, csvParam) {
    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            contentElement.innerHTML = renderFn(data, csvParam);
        })
        .catch(err => {
            displayError(errorElement, err);
            contentElement.innerHTML = '';
        });
}

function markDoneAndRefresh(context) {
    const { apiBaseUrl, taskId, csvParam, taskElement, errorElement, apiUrl } = context;
    const doneUrl = buildDoneUrl(apiBaseUrl, taskId, csvParam);

    return fetch(doneUrl, { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                return response.json().then(body => {
                    throw new Error(body.error || `HTTP ${response.status}`);
                });
            }
        })
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
    console.assert(taskElement, 'Missing #task element in task.html');
    console.assert(errorElement, 'Missing #error element in task.html');
    const { taskId, csvParam } = getQueryParams();
    const apiUrl = buildApiUrl(apiBaseUrl, taskId, csvParam);

    function makeContextHref(contextName, csvParam) {
        return csvParam
            ? `context.html?context=${encodeURIComponent(contextName)}&csv=${encodeURIComponent(csvParam)}`
            : `context.html?context=${encodeURIComponent(contextName)}`;
    }

    fetchJson(apiUrl)
        .then(task => {
            displayTask(taskElement, errorElement, task);
            const contextLink = document.getElementById('contextLink');
            if (contextLink) {
                contextLink.href = makeContextHref(task.context, csvParam);
                contextLink.textContent = task.context;
            }
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

function renderTaskLinks(tasks, csvParam) {
    if (tasks.length === 0) {
        return '<p>No tasks due.</p>';
    }

    const sorted = tasks.sort((a, b) => b.coins - a.coins);

    const rows = sorted.map(task => {
        const href = csvParam
            ? `task.html?id=${task.id}&csv=${encodeURIComponent(csvParam)}`
            : `task.html?id=${task.id}`;
        return `<tr><td>${task.id}</td><td><a href="${href}">${task.description}</a></td><td>${task.coins}</td></tr>`;
    }).join('');

    return `\
<table><thead><tr><th>ID</th><th>Description</th><th>Coins</th></tr></thead>\
<tbody>${rows}</tbody></table>`;
}

function initContextPage(apiBaseUrl) {
    const tasksElement = document.getElementById('tasks');
    const errorElement = document.getElementById('error');
    const contextNameElement = document.getElementById('contextName');
    console.assert(tasksElement, 'Missing #tasks element in context.html');
    console.assert(errorElement, 'Missing #error element in context.html');
    console.assert(contextNameElement, 'Missing #contextName element in context.html');
    const params = new URL(window.location).searchParams;
    const contextName = params.get('context');
    const csvParam = params.get('csv');

    if (contextName) {
        contextNameElement.textContent = contextName;
    }

    const listUrl = buildTasksByContextUrl(apiBaseUrl, contextName, csvParam);

    fetch(listUrl)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(taskIds => {
            const detailUrls = taskIds.map(id => buildApiUrl(apiBaseUrl, id, csvParam));
            return Promise.all(detailUrls.map(url => fetchJson(url)));
        })
        .then(tasks => {
            tasksElement.innerHTML = renderTaskLinks(tasks, csvParam);
            errorElement.hidden = true;
        })
        .catch(err => {
            displayError(errorElement, err);
            tasksElement.innerHTML = '';
        });
}

function initIndexPage(apiBaseUrl) {
    const contextsElement = document.getElementById('contexts');
    const errorElement = document.getElementById('error');
    console.assert(contextsElement, 'Missing #contexts element in index.html');
    console.assert(errorElement, 'Missing #error element in index.html');
    const { csvParam } = getQueryParams();
    const url = buildContextUrl(apiBaseUrl, csvParam);

    _fetchAndRender(url, renderContextList, contextsElement, errorElement, csvParam);
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

function _selfCheck() {
    var required = [
        'buildApiUrl', 'buildDoneUrl', 'renderTask', 'renderError',
        'fetchJson', 'markDoneAndRefresh', 'initTaskPage',
        'initContextPage', 'initIndexPage', 'renderTaskLinks',
        'renderContextList',
    ];
    required.forEach(function (name) {
        console.assert(
            typeof window[name] !== 'undefined',
            'Missing function: ' + name
        );
    });
}

document.addEventListener('DOMContentLoaded', () => {
    _selfCheck();
    initPage();
});
