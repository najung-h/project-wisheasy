document.addEventListener('DOMContentLoaded', () => {
    loadPriorityOrder();
    setupDragAndDrop();
});

function setupDragAndDrop() {
    const list = document.getElementById('priorityList');
    let draggedItem = null;

    list.addEventListener('dragstart', (e) => {
        draggedItem = e.target;
        setTimeout(() => {
            e.target.classList.add('dragging');
        }, 0);
    });

    list.addEventListener('dragend', (e) => {
        setTimeout(() => {
            draggedItem.classList.remove('dragging');
            draggedItem = null;
        }, 0);
    });

    list.addEventListener('dragover', (e) => {
        e.preventDefault();
        const afterElement = getDragAfterElement(list, e.clientY);
        const currentElement = document.querySelector('.dragging');
        if (afterElement == null) {
            list.appendChild(currentElement);
        } else {
            list.insertBefore(currentElement, afterElement);
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.priority-item:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function savePriorityOrder() {
    const list = document.getElementById('priorityList');
    const items = list.querySelectorAll('.priority-item');
    const priorityOrder = Array.from(items).map(item => {
        return item.dataset.priority;
    });

    localStorage.setItem('routePriority', JSON.stringify(priorityOrder));

    alert('우선순위가 저장되었습니다!\n\n' + priorityOrder.join(', '));
    console.log('Saved order:', priorityOrder);
}

function loadPriorityOrder() {
    const list = document.getElementById('priorityList');
    const savedOrder = JSON.parse(localStorage.getItem('routePriority'));

    if (savedOrder) {
        console.log('Loaded order:', savedOrder);
        // Reorder the elements based on the saved order
        savedOrder.forEach(priority => {
            const element = list.querySelector(`[data-priority="${priority}"]`);
            if (element) {
                list.appendChild(element);
            }
        });
    }
}

function goBack() {
    if (window.history.length > 1) {
        window.history.back();
    } else {
        window.location.href = 'main.html';
    }
}
