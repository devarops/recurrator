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
