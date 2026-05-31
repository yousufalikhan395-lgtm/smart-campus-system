// Smart Campus - Frontend Scripts

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Q4: Real-time validation for student IDs input
    const studentIdsInput = document.getElementById('student_ids');
    if (studentIdsInput) {
        studentIdsInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/[^0-9,\s]/g, '');
        });
    }

    // Q7: Directory path hint on focus
    const dirPathInput = document.getElementById('directory_path');
    if (dirPathInput) {
        dirPathInput.addEventListener('focus', function() {
            this.placeholder = "Example: C:/Users/YourName/Documents or /home/user/projects";
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});