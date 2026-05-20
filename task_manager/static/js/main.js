// Основной файл скриптов системы Task.ЦС
document.addEventListener('DOMContentLoaded', function() {
    // Сюда будем переносить инлайн-скрипты по мере обработки страниц
});

// Автоматическая стилизация полей форм Django под Bootstrap 5
document.querySelectorAll('form input, form select, form textarea').forEach(input => {
    // Игнорируем скрытые поля, кнопки и submit
    if (['submit', 'button', 'hidden'].includes(input.type)) return;

    if (input.type === 'checkbox' || input.type === 'radio') {
        input.classList.add('form-check-input');
        
        // Для чекбоксов в Bootstrap родителю желательно добавить класс form-check
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