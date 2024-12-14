document.addEventListener('DOMContentLoaded', () => {
    const emailList = document.getElementById('email-list');

    // Fetch email summaries from the backend
    fetch('/api/emails')
        .then(response => response.json())
        .then(data => {
            data.forEach(email => {
                const emailItem = document.createElement('div');
                emailItem.className = 'email-item';

                const emailSubject = document.createElement('h2');
                emailSubject.textContent = email.subject;

                const emailSummary = document.createElement('p');
                emailSummary.textContent = email.summary;

                const emailCategory = document.createElement('p');
                emailCategory.className = 'category';
                emailCategory.textContent = `Category: ${email.category}`;

                emailItem.appendChild(emailSubject);
                emailItem.appendChild(emailSummary);
                emailItem.appendChild(emailCategory);

                emailList.appendChild(emailItem);
            });
        })
        .catch(error => {
            console.error('Error fetching email summaries:', error);
        });
});
