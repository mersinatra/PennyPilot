// static/js/scripts.js

// Confirm before deleting a transaction or budget
function confirmDelete() {
    return confirm('Are you sure you want to delete this item? This action cannot be undone.');
}

function showToast(message, type) {
    let toastHTML = `
    <div class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    </div>`;
    document.getElementById('toast-container').innerHTML += toastHTML;
    let toastElement = document.querySelector('#toast-container .toast:last-child');
    let toast = new bootstrap.Toast(toastElement);
    toast.show();
}

// static/js/scripts.js

// Confirm before deleting a transaction or budget
function confirmDelete() {
    return confirm('Are you sure you want to delete this item? This action cannot be undone.');
}

// Initialize Bootstrap tooltips globally
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
