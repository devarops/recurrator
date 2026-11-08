const SCOPES_ACTIVE = false; // S1 — set true when the API returns a scope for each context.

const SCOPE_TILES = [
    { scope: 'work', label: 'Work', emoji: '💼' },
    { scope: 'personal', label: 'Personal', emoji: '🏡' },
    { scope: 'both', label: 'Both', emoji: '🔀' },
    { scope: 'all', label: 'All', emoji: '🗂️' },
];

function buildUrlWithParams(path, csvParam) {
    return csvParam ? `${path}?csv=${encodeURIComponent(csvParam)}` : path;
}

function buildApiUrl(taskId, csvParam) {
    return buildUrlWithParams(`/task/${taskId}`, csvParam);
}

function buildDoneUrl(taskId, csvParam) {
    return buildUrlWithParams(`/task/${taskId}/done`, csvParam);
}

function fetchJson(url, options = {}) {
    return fetch(url, options).then((response) => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    });
}

function currentParams() {
    return new URL(window.location).searchParams;
}

function getCsvParam() {
    return currentParams().get('csv');
}

function readScope() {
    return currentParams().get('scope') || 'all';
}

function pageHref(page, extra = {}) {
    const params = new URLSearchParams();
    const current = currentParams();
    ['csv', 'date'].forEach((key) => {
        const value = current.get(key);
        if (value) params.set(key, value);
    });
    Object.keys(extra).forEach((key) => {
        const value = extra[key];
        if (value !== undefined && value !== null && value !== '') {
            params.set(key, value);
        }
    });
    const query = params.toString();
    return query ? `${page}?${query}` : page;
}

function getTodayISO() {
    const pinned = currentParams().get('date');
    if (pinned && /^\d{4}-\d{2}-\d{2}$/.test(pinned)) {
        return pinned;
    }
    return new Intl.DateTimeFormat('en-CA', {
        timeZone: 'America/Los_Angeles',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).format();
}

function buildContextUrl() {
    const url = `/context/?date=${getTodayISO()}`;
    const csv = getCsvParam();
    return csv ? `${url}&csv=${encodeURIComponent(csv)}` : url;
}

function buildTasksByContextUrl(contextName) {
    const url = `/context/${encodeURIComponent(contextName)}?date=${getTodayISO()}`;
    const csv = getCsvParam();
    return csv ? `${url}&csv=${encodeURIComponent(csv)}` : url;
}

function applyScope(contexts, scope) {
    if (!SCOPES_ACTIVE) {
        return contexts;
    }
    return contexts.filter((context) => context.scope === scope);
}

function showContent(errorElement, contentElement) {
    errorElement.hidden = true;
    contentElement.hidden = false;
}

function showError(errorElement, contentElement, error) {
    console.error(error);
    errorElement.innerHTML = ui.renderError(error);
    errorElement.hidden = false;
    contentElement.hidden = true;
    const retry = errorElement.querySelector('[data-retry]');
    if (retry) {
        retry.addEventListener('click', () => window.location.reload());
    }
}

function breadcrumbItems(scope, context, taskId) {
    const items = [{ label: 'Recurrator', href: pageHref('index.html') }];
    if (scope !== undefined && scope !== null) {
        items.push({
            label: ui.scopeLabel(scope),
            href: pageHref('scope.html', { scope }),
        });
    }
    if (context !== undefined && context !== null) {
        items.push({
            label: context,
            href: pageHref('context.html', { context, scope }),
        });
    }
    if (taskId !== undefined && taskId !== null) {
        items.push({ label: '#' + taskId });
    }
    return items;
}

function initHomePage() {
    const headerElement = document.getElementById('pageHeader');
    const scopesElement = document.getElementById('scopes');
    const errorElement = document.getElementById('error');

    headerElement.innerHTML = ui.renderBreadcrumb(breadcrumbItems());
    scopesElement.innerHTML = ui.renderSkeleton('tiles');

    fetchJson(buildContextUrl())
        .then((contexts) => {
            const names = contexts.slice(0, 4);
            scopesElement.innerHTML = SCOPE_TILES.map((tile) => {
                const isAll = tile.scope === 'all';
                return ui.renderScopeTile({
                    scope: tile.scope,
                    label: tile.label,
                    emoji: tile.emoji,
                    dueCount: isAll ? contexts.length : null,
                    names: isAll ? names : [],
                    href: pageHref('scope.html', { scope: tile.scope }),
                });
            }).join('');
            showContent(errorElement, scopesElement);
        })
        .catch((error) => showError(errorElement, scopesElement, error));
}

function initScopePage() {
    const headerElement = document.getElementById('pageHeader');
    const contextsElement = document.getElementById('contexts');
    const errorElement = document.getElementById('error');
    const scope = readScope();

    headerElement.innerHTML = ui.renderBreadcrumb(breadcrumbItems(scope));
    contextsElement.innerHTML = ui.renderSkeleton('grid');

    fetchJson(buildContextUrl())
        .then((contexts) => {
            const filtered = applyScope(contexts, scope);
            if (filtered.length === 0) {
                contextsElement.innerHTML = ui.renderEmpty('grid');
            } else {
                contextsElement.innerHTML = ui.renderScopeGrid(
                    filtered.map((name) => ({
                        name,
                        href: pageHref('context.html', { context: name, scope }),
                    })),
                    scope
                );
            }
            showContent(errorElement, contextsElement);
        })
        .catch((error) => showError(errorElement, contextsElement, error));
}

function initContextPage() {
    const headerElement = document.getElementById('pageHeader');
    const tasksElement = document.getElementById('tasks');
    const errorElement = document.getElementById('error');
    const context = currentParams().get('context');
    const scope = readScope();
    const csvParam = getCsvParam();

    headerElement.innerHTML = ui.renderBreadcrumb(breadcrumbItems(scope, context || ''));
    tasksElement.innerHTML = ui.renderSkeleton('list');

    fetchJson(buildTasksByContextUrl(context))
        .then((taskIds) => Promise.all(taskIds.map((id) => fetchJson(buildApiUrl(id, csvParam)))))
        .then((tasks) => {
            tasks.sort((a, b) => b.coins - a.coins);
            const decorated = tasks.map((task) => ({
                ...task,
                href: pageHref('task.html', { id: task.id, scope }),
            }));
            if (decorated.length === 0) {
                tasksElement.innerHTML = ui.renderEmpty('list', {
                    backHref: pageHref('scope.html', { scope }),
                    backLabel: ui.scopeLabel(scope),
                });
            } else {
                tasksElement.innerHTML = ui.renderTaskList(decorated);
            }
            showContent(errorElement, tasksElement);
        })
        .catch((error) => showError(errorElement, tasksElement, error));
}

function decorateTask(task) {
    return {
        ...task,
        today: getTodayISO(),
    };
}

function loadTask(taskId, taskElement, errorElement) {
    const headerElement = document.getElementById('pageHeader');
    const scope = readScope();
    fetchJson(buildApiUrl(taskId, getCsvParam()))
        .then((task) => {
            const decorated = decorateTask(task);
            if (headerElement) {
                headerElement.innerHTML = ui.renderBreadcrumb(
                    breadcrumbItems(scope, decorated.context, decorated.id)
                );
            }
            taskElement.innerHTML = ui.renderMonsterCard(decorated);
            showContent(errorElement, taskElement);
            attachDoneHandler(decorated, taskElement, errorElement);
        })
        .catch((error) => showError(errorElement, taskElement, error));
}

function attachDoneHandler(task, taskElement, errorElement) {
    const button = document.getElementById('doneBtn');
    if (!button || button.disabled) {
        return;
    }
    button.addEventListener('click', () => {
        const label = document.getElementById('doneLabel');
        const saveError = document.getElementById('saveError');
        button.disabled = true;
        if (label) label.textContent = 'Saving…';

        fetch(buildDoneUrl(task.id, getCsvParam()), { method: 'POST' })
            .then((response) => {
                if (!response.ok) {
                    return response.json().then((body) => {
                        throw new Error(body.error || `HTTP ${response.status}`);
                    });
                }
            })
            .then(() => loadTask(task.id, taskElement, errorElement))
            .catch((error) => {
                console.error(error);
                button.disabled = false;
                if (label) label.textContent = '✓ Mark as Done';
                if (saveError) saveError.hidden = false;
            });
    });
}

function initTaskPage() {
    const taskElement = document.getElementById('task');
    const errorElement = document.getElementById('error');
    const taskId = currentParams().get('id');
    taskElement.innerHTML = ui.renderSkeleton('card');
    loadTask(taskId, taskElement, errorElement);
}

function initPage() {
    if (document.getElementById('scopes')) {
        initHomePage();
        return;
    }
    if (document.getElementById('contexts')) {
        initScopePage();
        return;
    }
    if (document.getElementById('tasks')) {
        initContextPage();
        return;
    }
    initTaskPage();
}

document.addEventListener('DOMContentLoaded', () => {
    initPage();
});
