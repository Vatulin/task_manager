document.addEventListener('DOMContentLoaded', function() {});

document.querySelectorAll('form input, form select, form textarea').forEach(input => {
    if (['submit', 'button', 'hidden'].includes(input.type)) return;

    if (input.type === 'checkbox' || input.type === 'radio') {
        input.classList.add('form-check-input');
        const container = input.closest('.field-container');
        if (container) {
            container.classList.add('form-check', 'ms-1');
        }
    } else if (input.tagName.toLowerCase() === 'select') {
        input.classList.add('form-select');
    } else {
        input.classList.add('form-control');
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const kanbanBoard = document.getElementById('kanban-board');
    if (!kanbanBoard) return; // Скрипт инициализируется только на странице Канбана

    const cards = document.querySelectorAll('.kanban-card');
    const columns = document.querySelectorAll('.kanban-column');
    const csrfToken = kanbanBoard.dataset.csrf;

    let draggedCard = null;

    cards.forEach(card => {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });

    columns.forEach(column => {
        column.addEventListener('dragover', handleDragOver);
        column.addEventListener('dragenter', handleDragEnter);
        column.addEventListener('dragleave', handleDragLeave);
        column.addEventListener('drop', handleDrop);
    });

    function handleDragStart(e) {
        draggedCard = this;
        this.classList.add('kanban-card-dragging');
        e.dataTransfer.setData('text/plain', this.dataset.taskId);
    }

    function handleDragEnd() {
        this.classList.remove('kanban-card-dragging');
        columns.forEach(col => col.classList.remove('kanban-column-hover'));
    }

    function handleDragOver(e) {
        e.preventDefault();
    }

    function handleDragEnter(e) {
        e.preventDefault();
        this.classList.add('kanban-column-hover');
    }

    function handleDragLeave() {
        this.classList.remove('kanban-column-hover');
    }

    function handleDrop(e) {
    e.preventDefault();
    this.classList.remove('kanban-column-hover');

    const taskId = e.dataTransfer.getData('text/plain');
    const newStatus = this.dataset.status;
    const targetContainer = this.querySelector('.kanban-cards-container');

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value 
                   || document.getElementById('kanban-board')?.dataset?.csrf;

    if (!taskId || !newStatus) {
        console.error('Отсутствует task_id или status');
        return;
    }

    fetch('/analytics/kanban/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ task_id: taskId, status: newStatus })
    })
    .then(async response => {
        console.log('Статус ответа:', response.status);
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Получено не JSON:', text.substring(0, 200));
            throw new Error(`Сервер вернул не JSON: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Ответ сервера:', data);
        
        if (data.status === 'success') {
            const cardElement = document.querySelector(`.kanban-card[data-task-id="${taskId}"]`);
            
            if (cardElement && targetContainer) {
                targetContainer.appendChild(cardElement);
                updateCounters();
                console.log('Карточка перемещена в DOM');
            } else {
                console.error('Карточка или контейнер не найдены в DOM');
            }
        } else {
            alert('Ошибка: ' + (data.message || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('🔥 Ошибка fetch:', error);
        alert(`Ошибка при обновлении статуса:\n${error.message}`);
    });
}

    function updateCounters() {
        columns.forEach(col => {
            const currentCount = col.querySelectorAll('.kanban-card').length;
            const counterElement = col.querySelector('.column-count');
            if (counterElement) {
                counterElement.textContent = currentCount;
            }
        });
    }
});

function sendStatusUpdate(taskId, newStatus) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    fetch('/tasks/update-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            task_id: taskId,
            status: newStatus
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Произошла ошибка при обработке запроса сервером');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            console.log('Данные успешно сохранены:', data.message);
        } else {
            alert('Ошибка сервера: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Ошибка выполнения Fetch:', error);
        alert('Ошибка при перемещении карточки\nНе удалось связаться с сервером. Проверьте сеть.');
    });
}