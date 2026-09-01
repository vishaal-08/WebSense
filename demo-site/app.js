// Demo App Submit Handler
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('signupForm');
  const submitBtn = document.getElementById('submitBtn');
  const statusMsg = document.getElementById('statusMessage');

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      // If WebSense allowed submission to reach here, show success message
      if (statusMsg) {
        statusMsg.classList.remove('hidden');
        submitBtn.disabled = true;
        submitBtn.innerText = "Account Created!";
      }
    });
  }
});
