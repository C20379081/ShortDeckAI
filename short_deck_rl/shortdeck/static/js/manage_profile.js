// Get elements
var modal = document.getElementById("passwordChangeModal");
var btn = document.getElementById("changePasswordButton");
var span = document.getElementsByClassName("close")[0];

btn.onclick = function() {
    modal.style.display = "block";
}
span.onclick = function() {
    modal.style.display = "none";
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("passwordChangeModal").style.display = "none";
});

// JS to change the password of the user, various errors pop up when the passwords dont match or the password is too similar to the username
document.getElementById("passwordChangeForm").onsubmit = function(event) {
    event.preventDefault(); 

    var form = this;
    var actionUrl = form.getAttribute("action"); 

    var formData = new FormData(form);

    fetch(actionUrl, {
        method: 'POST',
        body: formData,
        credentials: 'include',
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert("Password changed successfully.");
            modal.style.display = "none"; 
        } else {
            const firstErrorKey = Object.keys(data.errors)[0]; 
            const firstErrorMessage = data.errors[firstErrorKey][0].message; 
            alert("Failed to change password. Error: " + firstErrorMessage);
        }
    })
    
    .catch(error => console.error('Error:', error));
};
