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