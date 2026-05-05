function buildApiUrl(baseUrl, taskId, csvParam) {
    return csvParam
        ? `${baseUrl}/task/${taskId}?csv=${encodeURIComponent(csvParam)}`
        : `${baseUrl}/task/${taskId}`;
}

function buildDoneUrl(baseUrl, taskId, csvParam) {
    return csvParam
        ? `${baseUrl}/task/${taskId}/done?csv=${encodeURIComponent(csvParam)}`
        : `${baseUrl}/task/${taskId}/done`;
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

function fetchTask(apiUrl) {
    return fetch(apiUrl).then(r => r.json());
}

function markTaskDone(apiUrl) {
    return fetch(apiUrl, { method: 'POST' }).then(r => r.json());
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

function init(apiBaseUrl) {
    const { taskElement, errorElement } = getDomElements();
    const { taskId, csvParam } = getQueryParams();
    const apiUrl = buildApiUrl(apiBaseUrl, taskId, csvParam);

    fetchTask(apiUrl)
        .then(task => {
            taskElement.innerHTML = renderTask(task);
            errorElement.hidden = true;

            // Attach click handler to Done button
            const doneBtn = document.getElementById('doneBtn');
            doneBtn.addEventListener('click', () => {
                const doneUrl = buildDoneUrl(apiBaseUrl, taskId, csvParam);
                markTaskDone(doneUrl)
                    .then(() => {
                        // Reload the task to show updated data
                        fetchTask(apiUrl)
                            .then(updatedTask => {
                                taskElement.innerHTML = renderTask(updatedTask);
                                const newDoneBtn = document.getElementById('doneBtn');
                                newDoneBtn.addEventListener('click', arguments.callee);
                            });
                    })
                    .catch(err => {
                        errorElement.innerHTML = renderError(err);
                        errorElement.hidden = false;
                    });
            });
        })
        .catch(err => {
            errorElement.innerHTML = renderError(err);
            errorElement.hidden = false;
        });
}

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    init('http://localhost:8000');
});
