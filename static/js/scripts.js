    // Additional Toggle for All Modals (Optional)
    var recurringCheckboxes = document.querySelectorAll('.is-recurring-checkbox');
    recurringCheckboxes.forEach(function(checkbox) {
        var recurringFields = checkbox.closest('form').querySelector('.recurring-fields');

        function toggleRecurringFields() {
            if (checkbox.checked) {
                recurringFields.style.display = 'block';
            } else {
                recurringFields.style.display = 'none';
            }
        }

        toggleRecurringFields();
        checkbox.addEventListener('change', toggleRecurringFields);
    });
    

    // Handle Edit Budget Modal if exists
    var editBudgetModal = document.getElementById('editBudgetModal');
    if (editBudgetModal) {
        editBudgetModal.addEventListener('show.bs.modal', function (event) {
            var button = event.relatedTarget; // Button that triggered the modal
            var budgetId = button.getAttribute('data-id');
            var categoryId = button.getAttribute('data-category');
            var amount = button.getAttribute('data-amount');
            var month = button.getAttribute('data-month');

            // Get the form inside the modal
            var form = editBudgetModal.querySelector('form');

            // Set the form action to the appropriate route
            form.action = '/edit_budget/' + budgetId;

            // Set the form fields
            form.querySelector('select[name="category"]').value = categoryId;
            form.querySelector('input[name="amount"]').value = amount;
            form.querySelector('input[name="month"]').value = month;
        });
    }