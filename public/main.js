function buildApiUrl(baseUrl, taskId, csvParam) {
    return csvParam
        ? `${baseUrl}/task/${taskId}?csv=${encodeURIComponent(csvParam)}`
        : `${baseUrl}/task/${taskId}`;
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
    `;
}

function renderError(error) {
    return `Error: ${error.message}`;
}

function fetchTask(apiUrl) {
    return fetch(apiUrl).then(r => r.json());
}

function getQueryParams() {
    return {
        taskId: new URL(window.location).searchParams.get('id'),
        csvParam: new URL(window.location).searchParams.get('csv')
    };
}

function init(apiBaseUrl) {
    const taskElement = document.getElementById('task');
    const errorElement = document.getElementById('error');
    const { taskId, csvParam } = getQueryParams();
    const apiUrl = buildApiUrl(apiBaseUrl, taskId, csvParam);

    fetchTask(apiUrl)
        .then(task => {
            taskElement.innerHTML = renderTask(task);
        })
        .catch(err => {
            errorElement.innerHTML = renderError(err);
        });
}
