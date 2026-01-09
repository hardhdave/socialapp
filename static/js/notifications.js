// Notification handling functionality

// Poll for new notifications every 30 seconds
setInterval(updateNotificationCount, 30000);

function updateNotificationCount() {
  fetch("/api/notifications/unread-count")
    .then((response) => response.json())
    .then((data) => {
      const badge = document.getElementById("notification-count");
      if (badge) {
        if (data.count > 0) {
          badge.textContent = data.count;
          badge.style.display = "block";
        } else {
          badge.style.display = "none";
        }
      }
    })
    .catch((error) => console.error("Error updating notifications:", error));
}

// Mark notification as read when clicked
function markNotificationAsRead(notificationId) {
  fetch(`/api/notifications/${notificationId}/mark-read`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        updateNotificationCount();
      }
    })
    .catch((error) =>
      console.error("Error marking notification as read:", error)
    );
}
