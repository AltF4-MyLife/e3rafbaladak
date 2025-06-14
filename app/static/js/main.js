/**
 * e3rafbaladak.com - Main JavaScript
 * A national initiative to educate students about their country
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Animate stats counters if they exist
    animateCounters();

    // Handle form validations
    setupFormValidations();

    // Setup quiz functionality if on quiz page
    setupQuiz();

    // Setup media rating system if on media detail page
    setupMediaRating();

    // Setup notification read functionality
    setupNotifications();

    // Setup language switcher
    setupLanguageSwitcher();
});

/**
 * Animate counter elements with a counting effect
 */
function animateCounters() {
    const counters = document.querySelectorAll('.counter');
    
    if (counters.length === 0) return;

    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 2000; // ms
        const step = Math.ceil(target / (duration / 16)); // 60fps
        let current = 0;

        const updateCounter = () => {
            current += step;
            if (current >= target) {
                counter.textContent = target.toLocaleString();
                return;
            }
            counter.textContent = current.toLocaleString();
            requestAnimationFrame(updateCounter);
        };

        // Start animation when element is in viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        observer.observe(counter);
    });
}

/**
 * Setup form validations using Bootstrap's validation classes
 */
function setupFormValidations() {
    // Fetch all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');

    if (forms.length === 0) return;

    // Loop over them and prevent submission
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Setup quiz functionality
 */
function setupQuiz() {
    const quizForm = document.getElementById('quiz-form');
    
    if (!quizForm) return;

    quizForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Collect answers
        const formData = new FormData(quizForm);
        const answers = {};
        
        for (let [key, value] of formData.entries()) {
            if (key.startsWith('question_')) {
                const questionId = key.split('_')[1];
                answers[questionId] = value;
            }
        }
        
        // Submit answers via AJAX
        fetch(quizForm.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ answers: answers })
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                // Show results on the same page
                document.getElementById('quiz-questions').style.display = 'none';
                document.getElementById('quiz-results').style.display = 'block';
                document.getElementById('quiz-score').textContent = data.score;
                document.getElementById('quiz-total').textContent = data.total;
                
                // Highlight correct and incorrect answers
                data.questions.forEach(question => {
                    const resultItem = document.createElement('div');
                    resultItem.className = 'mb-3';
                    resultItem.innerHTML = `
                        <p><strong>${question.text}</strong></p>
                        <p>Your answer: <span class="${question.is_correct ? 'text-success' : 'text-danger'}">${question.user_answer}</span></p>
                        ${!question.is_correct ? `<p>Correct answer: <span class="text-success">${question.correct_answer}</span></p>` : ''}
                    `;
                    document.getElementById('quiz-answers').appendChild(resultItem);
                });
            }
        })
        .catch(error => {
            console.error('Error submitting quiz:', error);
            alert('There was an error submitting your quiz. Please try again.');
        });
    });
}

/**
 * Setup media rating system
 */
function setupMediaRating() {
    const ratingForm = document.getElementById('rating-form');
    
    if (!ratingForm) return;

    const ratingInputs = ratingForm.querySelectorAll('input[name="rating"]');
    const mediaId = ratingForm.getAttribute('data-media-id');
    
    ratingInputs.forEach(input => {
        input.addEventListener('change', function() {
            const rating = this.value;
            
            // Submit rating via AJAX
            fetch('/content/media/' + mediaId + '/rate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ rating: rating })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update average rating display
                    document.getElementById('average-rating').textContent = data.average_rating;
                    document.getElementById('rating-count').textContent = data.rating_count;
                    
                    // Show success message
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
                    alertDiv.innerHTML = `
                        ${data.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    ratingForm.appendChild(alertDiv);
                    
                    // Auto-dismiss after 3 seconds
                    setTimeout(() => {
                        const bsAlert = new bootstrap.Alert(alertDiv);
                        bsAlert.close();
                    }, 3000);
                }
            })
            .catch(error => {
                console.error('Error submitting rating:', error);
                alert('There was an error submitting your rating. Please try again.');
            });
        });
    });
}

/**
 * Setup notification read functionality
 */
function setupNotifications() {
    const notificationItems = document.querySelectorAll('.notification-item');
    
    if (notificationItems.length === 0) return;

    notificationItems.forEach(item => {
        item.addEventListener('click', function() {
            const notificationId = this.getAttribute('data-notification-id');
            
            // Mark as read via AJAX
            fetch('/notifications/' + notificationId + '/read', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI to show notification as read
                    this.classList.remove('unread');
                    this.classList.add('read');
                    
                    // Update unread count in navbar if it exists
                    const unreadBadge = document.querySelector('.notification-badge');
                    if (unreadBadge) {
                        const currentCount = parseInt(unreadBadge.textContent);
                        if (currentCount > 1) {
                            unreadBadge.textContent = currentCount - 1;
                        } else {
                            unreadBadge.style.display = 'none';
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error marking notification as read:', error);
            });
        });
    });
}

/**
 * Setup language switcher
 */
function setupLanguageSwitcher() {
    const languageSwitcher = document.getElementById('language-switcher');
    
    if (!languageSwitcher) return;

    languageSwitcher.addEventListener('change', function() {
        const selectedLanguage = this.value;
        
        // Create a form and submit it to change the language
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/set-language';
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'language';
        input.value = selectedLanguage;
        
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
    });
}

/**
 * Handle file uploads with preview
 */
function handleFileUpload(inputId, previewId) {
    const fileInput = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (!fileInput || !preview) return;

    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        
        if (file) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            
            reader.readAsDataURL(file);
        }
    });
}

/**
 * Export data to CSV
 */
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    
    if (!table) return;

    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Get the text content and escape double quotes
            let data = cols[j].textContent.replace(/"/g, '""');
            // Wrap with double quotes to handle commas within the text
            row.push('"' + data + '"');
        }
        
        csv.push(row.join(','));
    }
    
    const csvString = csv.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    
    // Create a download link and trigger it
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Generate PDF report
 */
function generatePDF(elementId, filename) {
    const element = document.getElementById(elementId);
    
    if (!element) return;

    // Show loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'text-center my-3';
    loadingIndicator.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Generating PDF...</p>';
    
    document.body.appendChild(loadingIndicator);
    
    // Use server-side endpoint to generate PDF
    fetch('/admin/generate-pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ 
            element_id: elementId,
            filename: filename
        })
    })
    .then(response => response.blob())
    .then(blob => {
        // Create a download link and trigger it
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.href = url;
        link.download = filename;
        link.click();
        
        // Remove loading indicator
        document.body.removeChild(loadingIndicator);
    })
    .catch(error => {
        console.error('Error generating PDF:', error);
        alert('There was an error generating the PDF. Please try again.');
        document.body.removeChild(loadingIndicator);
    });
}