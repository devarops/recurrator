(function () {
    'use strict';

    var ACCENTS = ['orange', 'yellow', 'green', 'aqua', 'blue', 'purple', 'red'];
    var SCOPE_ACCENTS = {
        work: 'blue',
        personal: 'green',
        both: 'purple',
        all: 'orange',
    };
    var SCOPE_LABELS = {
        all: 'All',
        work: 'Work',
        personal: 'Personal',
        both: 'Both',
    };
    var CONTEXT_META = {
        actividad: '🏃',
        admingeci: '🗄️',
        bycatchcode: '🐟',
        casa: '🏠',
        chores: '✅',
        doctoradoadmin: '🎓',
        electronica: '🔌',
        escritura: '✍️',
        estudio: '📚',
        gecicode: '🛰️',
        laptop: '💻',
        lectura: '📖',
        lider: '🧭',
        mandado: '🛒',
        telefono: '📱',
        tresminutos: '⏱️',
    };
    var HOME_ICON =
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">' +
        '<path d="M4 11.2 12 4l8 7.2V20a1 1 0 0 1-1 1h-4.5v-6h-5v6H5a1 1 0 0 1-1-1z" ' +
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>';

    function escapeHtml(value) {
        return String(value === null || value === undefined ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function escapeAttr(value) {
        return escapeHtml(value);
    }

    function accentFor(name) {
        var text = String(name || '').toLowerCase().trim();
        var sum = 0;
        for (var i = 0; i < text.length; i += 1) {
            sum += text.charCodeAt(i);
        }
        return ACCENTS[sum % ACCENTS.length];
    }

    function scopeLabel(scope) {
        return SCOPE_LABELS[String(scope || '').toLowerCase()] || 'All';
    }

    function monsterTitle(description) {
        var lines = String(description || '').replace(/\r\n/g, '\n').split('\n');
        var line = '';
        for (var i = 0; i < lines.length; i += 1) {
            if (lines[i].trim() !== '') {
                line = lines[i];
                break;
            }
        }
        line = line.replace(/^\s*(?:[-*+]\s+)?(?:\[[ xX]\]\s*)?/, '');
        line = line.replace(/^\s*\d+[.)]\s+/, '');
        line = line.replace(/^\s*#+\s*/, '');
        line = line.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1');
        line = line.replace(/[*_`~]/g, '');
        var words = line.trim().split(/\s+/).filter(Boolean).slice(0, 3);
        if (words.length === 0) {
            return '';
        }
        var text = words.join(' ');
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    function dueState(task) {
        if (!task || !task.due_date || !task.today) {
            return '';
        }
        return task.due_date <= task.today ? 'due' : 'not-due';
    }

    function dayNumber(iso) {
        var parts = iso.split('-').map(Number);
        return Date.UTC(parts[0], parts[1] - 1, parts[2]) / 86400000;
    }

    function daysBetween(from, to) {
        return Math.round(dayNumber(to) - dayNumber(from));
    }

    function isDoneRecently(latest, today) {
        if (!latest || !today) {
            return false;
        }
        return latest === today || daysBetween(today, latest) === -1;
    }

    function plural(count, singular, pluralWord) {
        return count === 1 ? singular : pluralWord;
    }

    function statusText(task) {
        if (!task.due_date) {
            return '';
        }
        if (isDoneRecently(task.latest_date, task.today)) {
            return task.latest_date === task.today ? 'Done today' : 'Done yesterday';
        }
        if (task.due_date < task.today) {
            var overdue = daysBetween(task.due_date, task.today);
            if (overdue < 30) {
                return 'Overdue by ' + overdue + ' ' + plural(overdue, 'day', 'days');
            }
            var overdueMonths = Math.floor(overdue / 30);
            return (
                'Overdue by ' + overdueMonths + ' ' + plural(overdueMonths, 'month', 'months')
            );
        }
        if (task.due_date === task.today) {
            return 'Due today';
        }
        var ahead = daysBetween(task.today, task.due_date);
        if (ahead <= 45) {
            return 'Due in ' + ahead + ' ' + plural(ahead, 'day', 'days');
        }
        var aheadMonths = Math.floor(ahead / 30);
        return 'Due in ' + aheadMonths + ' ' + plural(aheadMonths, 'month', 'months');
    }

    function statusKind(task) {
        if (!task.due_date) {
            return 'none';
        }
        if (isDoneRecently(task.latest_date, task.today)) {
            return 'done';
        }
        return task.due_date <= task.today ? 'due' : 'future';
    }

    function renderInline(text) {
        var out = escapeHtml(text);
        out = out.replace(
            /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
            '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
        out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        out = out.replace(/_([^_]+)_/g, '<em>$1</em>');
        return out;
    }

    function renderMarkdown(markdown) {
        var lines = String(markdown || '').replace(/\r\n/g, '\n').split('\n');
        var blocks = [];
        var paragraph = [];
        var list = null;

        function flushParagraph() {
            if (paragraph.length > 0) {
                blocks.push('<p>' + paragraph.join('<br>') + '</p>');
                paragraph = [];
            }
        }

        function flushList() {
            if (list && list.items.length > 0) {
                var className = list.type === 'check' ? ' class="check-list"' : '';
                blocks.push('<ul' + className + '>' + list.items.join('') + '</ul>');
            }
            list = null;
        }

        lines.forEach(function (line) {
            var trimmed = line.trim();
            if (trimmed === '') {
                flushParagraph();
                flushList();
                return;
            }
            var check = trimmed.match(/^[-*+]\s+\[([ xX])\]\s+(.*)$/);
            if (check) {
                flushParagraph();
                if (!list || list.type !== 'check') {
                    flushList();
                    list = { type: 'check', items: [] };
                }
                var checked = check[1].toLowerCase() === 'x' ? ' checked' : '';
                list.items.push(
                    '<li class="check-item"><input type="checkbox"' +
                        checked +
                        '> <span>' +
                        renderInline(check[2]) +
                        '</span></li>'
                );
                return;
            }
            var bullet = trimmed.match(/^[-*+]\s+(.*)$/);
            if (bullet) {
                flushParagraph();
                if (!list || list.type !== 'ul') {
                    flushList();
                    list = { type: 'ul', items: [] };
                }
                list.items.push('<li>' + renderInline(bullet[1]) + '</li>');
                return;
            }
            flushList();
            paragraph.push(renderInline(trimmed));
        });

        flushParagraph();
        flushList();
        return blocks.join('');
    }

    function renderSkeleton(kind) {
        if (kind === 'tiles') {
            var tiles = [];
            for (var i = 0; i < 4; i += 1) {
                tiles.push(
                    '<div class="skeleton-tile" aria-hidden="true">' +
                        '<div class="skeleton-disc"></div>' +
                        '<div class="skeleton-line skeleton-line--title"></div>' +
                        '<div class="skeleton-line"></div>' +
                        '<div class="skeleton-line skeleton-line--short"></div>' +
                        '</div>'
                );
            }
            return tiles.join('');
        }
        if (kind === 'grid') {
            var cards = [];
            for (var c = 0; c < 4; c += 1) {
                cards.push('<div class="skeleton-card"></div>');
            }
            return '<div class="context-grid" aria-hidden="true">' + cards.join('') + '</div>';
        }
        if (kind === 'list') {
            var rows = [];
            for (var r = 0; r < 6; r += 1) {
                rows.push('<div class="skeleton-row"></div>');
            }
            return '<div class="task-list" aria-hidden="true">' + rows.join('') + '</div>';
        }
        return '<div class="skeleton-monster" aria-hidden="true"></div>';
    }

    function renderEmpty(kind, ctx) {
        if (kind === 'grid') {
            return (
                '<div class="empty">' +
                '<p class="empty__title">You are victorious!</p>' +
                '<p class="empty__text">Every monster has been exterminated.</p>' +
                '</div>'
            );
        }
        var back = '';
        if (ctx && ctx.backHref) {
            back =
                '<a class="empty__link" href="' +
                escapeAttr(ctx.backHref) +
                '">Back to ' +
                escapeHtml(ctx.backLabel || 'contexts') +
                '</a>';
        }
        return (
            '<div class="empty">' +
            '<p class="empty__title">No monsters left here.</p>' +
            '<p class="empty__text">' +
            back +
            '</p>' +
            '</div>'
        );
    }

    function renderError() {
        return (
            '<div class="error-card" role="alert">' +
            "<p class=\"error-card__title\">Couldn't load</p>" +
            '<p class="error-card__text">Something went wrong. Try again.</p>' +
            '<button class="btn btn--secondary" type="button" data-retry>Try again</button>' +
            '</div>'
        );
    }

    function renderBreadcrumb(items) {
        var parts = items.map(function (item, index) {
            var last = index === items.length - 1;
            if (last || !item.href) {
                return '<span aria-current="page">' + escapeHtml(item.label) + '</span>';
            }
            return '<a href="' + escapeAttr(item.href) + '">' + escapeHtml(item.label) + '</a>';
        });
        return (
            '<nav class="breadcrumb" aria-label="Breadcrumb">' +
            parts.join('<span aria-hidden="true">/</span>') +
            '</nav>'
        );
    }

    function renderHomeHeader() {
        return (
            '<header class="page-header">' +
            '<h1 class="page-title">Recurrator</h1>' +
            '<p class="subtitle">Pick a scope to start</p>' +
            '</header>'
        );
    }

    function renderScopeHeader(options) {
        var subtitle = '';
        if (options.count !== null && options.count !== undefined) {
            subtitle =
                options.count === 0
                    ? 'Victorious'
                    : options.count +
                      ' ' +
                      plural(options.count, 'context', 'contexts') +
                      ' due';
        }
        return (
            '<header class="page-header scope-header">' +
            '<a class="home-button" href="' +
            escapeAttr(options.homeHref) +
            '" aria-label="Recurrator home">' +
            HOME_ICON +
            '</a>' +
            '<div><h1 class="page-title">' +
            escapeHtml(options.label) +
            '</h1>' +
            (subtitle ? '<p class="subtitle">' + subtitle + '</p>' : '') +
            '</div></header>'
        );
    }

    function renderContextHeader(options) {
        return (
            '<header class="page-header">' +
            renderBreadcrumb([
                { label: 'Recurrator', href: options.links.home },
                { label: options.scopeLabel, href: options.links.scope },
                { label: options.context || '' },
            ]) +
            '<h1 class="page-title">' +
            escapeHtml(options.context || '') +
            '</h1></header>'
        );
    }

    function renderScopeTile(tile) {
        var accent = SCOPE_ACCENTS[tile.scope] || 'orange';
        var long = String(tile.label).length > 7 ? ' tile__title--long' : '';
        var hasCount = tile.dueCount !== null && tile.dueCount !== undefined;
        var count = '';
        if (hasCount && tile.dueCount === 0) {
            count = '<p class="tile__count"><span class="tile__victorious">Victorious</span></p>';
        } else if (hasCount) {
            count =
                '<p class="tile__count"><span class="tile__due">' +
                tile.dueCount +
                ' ' +
                plural(tile.dueCount, 'context', 'contexts') +
                ' due</span> <span class="tile__today">· due today</span></p>';
        }
        var names = hasCount && tile.dueCount > 0 ? tile.names || [] : [];
        var items = names
            .map(function (name) {
                return (
                    '<li class="tile__name"><span class="dot accent-' +
                    accentFor(name) +
                    '" aria-hidden="true"></span>' +
                    escapeHtml(name) +
                    '</li>'
                );
            })
            .join('');
        var more = names.length > 0 ? tile.dueCount - names.length : 0;
        if (more > 0) {
            items += '<li class="tile__name tile__name--more">+' + more + ' more</li>';
        }
        var divider =
            hasCount && tile.dueCount > 0
                ? '<div class="tile__divider" aria-hidden="true"></div>'
                : '';
        return (
            '<a class="tile accent-' +
            accent +
            '" href="' +
            escapeAttr(tile.href) +
            '">' +
            '<div class="tile__head"><span class="disc" aria-hidden="true">' +
            tile.emoji +
            '</span><span class="tile__title' +
            long +
            '">' +
            escapeHtml(tile.label) +
            '</span></div>' +
            '<div class="tile__body">' +
            count +
            divider +
            '<ul class="tile__names">' +
            items +
            '</ul></div>' +
            '<div class="tile__footer"><span class="tile__open">OPEN</span>' +
            '<span class="tile__chevron" aria-hidden="true">›</span></div></a>'
        );
    }

    function renderScopeGrid(contexts, scope) {
        var cards = contexts
            .map(function (context) {
                var accent = accentFor(context.name);
                var emoji = CONTEXT_META[context.name] || '🗂️';
                var long = context.name.length > 10 ? ' context-card__title--long' : '';
                if (context.name.length > 12) {
                    long += ' context-card__title--xlong';
                }
                return (
                    '<a class="context-card" href="' +
                    escapeAttr(context.href) +
                    '"><span class="disc disc--small accent-' +
                    accent +
                    '" aria-hidden="true">' +
                    emoji +
                    '</span><span class="context-card__title' +
                    long +
                    '">' +
                    escapeHtml(context.name) +
                    '</span><span class="chevron accent-' +
                    accent +
                    '" aria-hidden="true">›</span></a>'
                );
            })
            .join('');
        return '<div class="context-grid" data-scope="' + escapeAttr(scope) + '">' + cards + '</div>';
    }

    function renderTaskList(tasks) {
        var rows = tasks
            .map(function (task) {
                return (
                    '<a class="task-row" href="' +
                    escapeAttr(task.href) +
                    '"><img class="task-row__thumb" src="monster-placeholder.png" alt="" width="40" height="40">' +
                    '<span class="task-row__title">' +
                    escapeHtml(monsterTitle(task.description)) +
                    '</span><span class="bounty" aria-label="' +
                    task.coins +
                    ' coins"><span class="bounty__dot" aria-hidden="true"></span>' +
                    '<span class="bounty__value">' +
                    task.coins +
                    '</span></span></a>'
                );
            })
            .join('');
        return '<div class="task-list">' + rows + '</div>';
    }

    function renderMonsterCard(task, options) {
        var interactive = !options || options.interactive !== false;
        var state = dueState(task);
        var stateClass = state ? 'monster-card--' + state : 'monster-card--none';
        var accent = accentFor(task.context);
        var title = monsterTitle(task.description);
        var doneRecent = isDoneRecently(task.latest_date, task.today);
        var doneLabel = doneRecent
            ? task.latest_date === task.today
                ? 'Done today ✓'
                : 'Done yesterday ✓'
            : '✓ Mark as Done';
        var doneClass = doneRecent ? 'btn btn--primary btn--done' : 'btn btn--primary';
        var buttonId = interactive ? ' id="doneBtn"' : '';
        var labelId = interactive ? ' id="doneLabel"' : '';
        var saveError = interactive
            ? '<p id="saveError" class="save-error" hidden>Didn\'t save. Try again.</p>'
            : '';
        var status = statusText(task);
        var statusLine = status
            ? '<p class="status-line status-line--' +
              statusKind(task) +
              '">' +
              escapeHtml(status) +
              '</p>'
            : '';
        var stats = [
            ['RECURRENCE', task.recurrence_days + ' days'],
            ['SKIP COUNT', task.skip_count],
            ['DUE DATE', task.due_date || '—'],
            ['LATEST DONE', task.latest_date || '—'],
        ]
            .map(function (pair) {
                return (
                    '<div class="stat"><span class="stat__label">' +
                    pair[0] +
                    '</span><span class="stat__value">' +
                    escapeHtml(String(pair[1])) +
                    '</span></div>'
                );
            })
            .join('');
        var links = task.links || {};
        var breadcrumb = renderBreadcrumb([
            { label: 'Recurrator', href: links.home },
            { label: task.scopeLabel || 'All', href: links.scope },
            { label: task.context, href: links.context },
            { label: '#' + task.id },
        ]);
        return (
            breadcrumb +
            '<article class="monster-card ' +
            stateClass +
            '">' +
            '<div class="monster-card__header">' +
            '<h1 class="monster-card__title">' +
            escapeHtml(title) +
            '</h1>' +
            '<div class="bounty-badge bounty-badge--' +
            (task.starred ? 'star' : 'circle') +
            '" role="img" aria-label="' +
            (task.starred ? 'Starred' : 'Not starred') +
            '"><span class="bounty-badge__shape">' +
            '<span class="bounty-badge__value">' +
            task.coins +
            '</span></span><span class="bounty-badge__label">BOUNTY</span></div>' +
            '<p class="monster-card__subtitle">' +
            escapeHtml(task.context) +
            ' · every ' +
            task.recurrence_days +
            ' days</p></div>' +
            '<div class="art-panel accent-' +
            accent +
            '"><span class="context-chip"><span aria-hidden="true">' +
            (CONTEXT_META[task.context] || '🗂️') +
            '</span>' +
            escapeHtml(task.context) +
            '</span><img class="art-panel__monster" src="monster-placeholder.png" alt="" width="139" height="139">' +
            '<span class="art-panel__shadow" aria-hidden="true"></span>' +
            '<span class="no-badge">No. ' +
            task.id +
            '</span></div>' +
            '<div class="stat-grid">' +
            stats +
            '</div>' +
            statusLine +
            '<div class="description">' +
            renderMarkdown(task.description) +
            '</div>' +
            '<p class="microtext">RCR-' +
            String(task.id).padStart(3, '0') +
            ' · ' +
            escapeHtml(task.context) +
            ' · ' +
            task.recurrence_days +
            'd</p></article>' +
            '<div class="actions"><button' +
            buttonId +
            ' class="' +
            doneClass +
            '" type="button"' +
            (doneRecent ? ' disabled' : '') +
            '><span' +
            labelId +
            ' aria-live="polite">' +
            doneLabel +
            '</span></button>' +
            saveError +
            '<button class="btn btn--secondary" type="button" aria-disabled="true">✎ Edit monster</button>' +
            '</div>'
        );
    }

    window.ui = {
        renderScopeTile: renderScopeTile,
        renderScopeGrid: renderScopeGrid,
        renderTaskList: renderTaskList,
        renderMonsterCard: renderMonsterCard,
        renderMarkdown: renderMarkdown,
        renderSkeleton: renderSkeleton,
        renderEmpty: renderEmpty,
        renderError: renderError,
        renderHomeHeader: renderHomeHeader,
        renderScopeHeader: renderScopeHeader,
        renderContextHeader: renderContextHeader,
        renderBreadcrumb: renderBreadcrumb,
        accentFor: accentFor,
        scopeLabel: scopeLabel,
        monsterTitle: monsterTitle,
        dueState: dueState,
    };
})();
