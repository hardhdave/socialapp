// Main JavaScript functionality for Joy

// CSRF token for AJAX requests
let csrfToken = "";

// Initialize the app
document.addEventListener("DOMContentLoaded", function () {
  initializeApp();
  loadNotificationCount();
});

function initializeApp() {
  // Get CSRF token if available
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  if (csrfMeta) {
    csrfToken = csrfMeta.getAttribute("content");
  }

  // Initialize file input previews
  initializeFileInputs();

  // Initialize auto-expanding textareas
  initializeTextareas();
}

// File input handling
function initializeFileInputs() {
  const fileInputs = document.querySelectorAll(".file-input");
  fileInputs.forEach((input) => {
    input.addEventListener("change", function (e) {
      const file = e.target.files[0];
      if (file) {
        previewFile(file, input);
      }
    });
  });
}

function previewFile(file, input) {
  const reader = new FileReader();
  const preview = document.createElement("div");
  preview.className = "file-preview";

  reader.onload = function (e) {
    if (file.type.startsWith("image/")) {
      preview.innerHTML = `<img src="${e.target.result}" style="max-width: 200px; max-height: 200px; border-radius: 5px; margin-top: 10px;">`;
    } else if (file.type.startsWith("video/")) {
      preview.innerHTML = `<video src="${e.target.result}" style="max-width: 200px; max-height: 200px; border-radius: 5px; margin-top: 10px;" controls></video>`;
    }
  };

  reader.readAsDataURL(file);

  // Remove existing preview
  const existingPreview = input.parentNode.querySelector(".file-preview");
  if (existingPreview) {
    existingPreview.remove();
  }

  input.parentNode.appendChild(preview);
}

// Auto-expanding textareas
function initializeTextareas() {
  const textareas = document.querySelectorAll(".post-textarea, .comment-input");
  textareas.forEach((textarea) => {
    textarea.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = this.scrollHeight + "px";
    });
  });
}

// Like/Unlike post
function toggleLike(postId) {
  fetch(`/post/${postId}/like`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const likeBtn = document.querySelector(
          `[data-post-id="${postId}"] .like-btn`
        );
        const likeCount = likeBtn.querySelector(".like-count");

        if (data.liked) {
          likeBtn.classList.add("liked");
        } else {
          likeBtn.classList.remove("liked");
        }

        likeCount.textContent = data.likes_count;
        showToast(data.message);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showToast("An error occurred", "error");
    });
}

// Add comment
function addComment(event, postId) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  fetch(`/post/${postId}/comment`, {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Clear the form
        form.reset();

        // Add comment to the list
        const commentsList = document.querySelector(`#comments-list-${postId}`);
        if (commentsList) {
          const commentHtml = createCommentHTML(data.comment);
          commentsList.insertAdjacentHTML("afterbegin", commentHtml);
        }

        // Update comment count
        const commentCount = document.querySelector(
          `[data-post-id="${postId}"] .action-btn .fas.fa-comment + span`
        );
        if (commentCount) {
          commentCount.textContent = data.comments_count;
        }

        showToast("Comment added successfully");
      } else {
        showToast(data.message, "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showToast("An error occurred", "error");
    });
}

function createCommentHTML(comment) {
  return `
        <div class="comment" data-comment-id="${comment.id}">
            <img src="${comment.author_avatar}" alt="${comment.author}" class="comment-avatar">
            <div class="comment-content">
                <div class="comment-author">${comment.author}</div>
                <div class="comment-text">${comment.content}</div>
                <div class="comment-time">${comment.time_ago}</div>
            </div>
        </div>
    `;
}

// Show/Hide comments
function showComments(postId) {
  const commentsSection = document.querySelector(`#comments-${postId}`);
  if (commentsSection) {
    if (commentsSection.style.display === "none") {
      commentsSection.style.display = "block";
      loadComments(postId);
    } else {
      commentsSection.style.display = "none";
    }
  }
}

function loadComments(postId) {
  const commentsList = document.querySelector(`#comments-list-${postId}`);
  if (commentsList && commentsList.children.length === 0) {
    // Load comments via AJAX
    fetch(`/api/posts/${postId}/comments`)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          data.comments.forEach((comment) => {
            const commentHtml = createCommentHTML(comment);
            commentsList.insertAdjacentHTML("beforeend", commentHtml);
          });
        }
      })
      .catch((error) => console.error("Error loading comments:", error));
  }
}

// Follow/Unfollow user
function followUser(username) {
  fetch(`/user/follow/${username}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Update follow button
        const followBtns = document.querySelectorAll(
          `button[onclick="followUser('${username}')"]`
        );
        followBtns.forEach((btn) => {
          btn.textContent = "Unfollow";
          btn.className = "btn btn-secondary";
          btn.setAttribute("onclick", `unfollowUser('${username}')`);
        });

        // Update follower count if on profile page
        updateFollowerCount(data.followers_count);

        showToast(data.message);
      } else {
        showToast(data.message, "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showToast("An error occurred", "error");
    });
}

function unfollowUser(username) {
  fetch(`/user/unfollow/${username}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Update follow button
        const unfollowBtns = document.querySelectorAll(
          `button[onclick="unfollowUser('${username}')"]`
        );
        unfollowBtns.forEach((btn) => {
          btn.innerHTML = '<i class="fas fa-user-plus"></i> Follow';
          btn.className = "btn btn-outline";
          btn.setAttribute("onclick", `followUser('${username}')`);
        });

        // Update follower count if on profile page
        updateFollowerCount(data.followers_count);

        showToast(data.message);
      } else {
        showToast(data.message, "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showToast("An error occurred", "error");
    });
}

function updateFollowerCount(count) {
  const followerCount = document.querySelector(".stat-number");
  if (followerCount) {
    followerCount.textContent = count;
  }
}

// Delete post
function deletePost(postId) {
  if (confirm("Are you sure you want to delete this post?")) {
    fetch(`/post/${postId}/delete`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
    })
      .then((response) => {
        if (response.ok) {
          // Remove post from DOM
          const postCard = document.querySelector(`[data-post-id="${postId}"]`);
          if (postCard) {
            postCard.remove();
          }
          showToast("Post deleted successfully");
        } else {
          showToast("Failed to delete post", "error");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showToast("An error occurred", "error");
      });
  }
}

// Share post
function sharePost(postId) {
  if (navigator.share) {
    navigator.share({
      title: "Check out this post",
      url: `/post/${postId}`,
    });
  } else {
    // Fallback: copy link to clipboard
    const url = `${window.location.origin}/post/${postId}`;
    navigator.clipboard.writeText(url).then(() => {
      showToast("Link copied to clipboard");
    });
  }
}

// Load notification count
function loadNotificationCount() {
  fetch("/api/notifications/unread-count")
    .then((response) => response.json())
    .then((data) => {
      const badge = document.getElementById("notification-count");
      if (badge && data.count > 0) {
        badge.textContent = data.count;
        badge.style.display = "block";
      }
    })
    .catch((error) => console.error("Error loading notifications:", error));
}

// Toast notifications
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;

  // Style the toast
  Object.assign(toast.style, {
    position: "fixed",
    top: "100px",
    right: "20px",
    padding: "1rem 1.5rem",
    borderRadius: "5px",
    color: "white",
    backgroundColor: type === "error" ? "#dc3545" : "#28a745",
    zIndex: "9999",
    opacity: "0",
    transition: "opacity 0.3s",
  });

  document.body.appendChild(toast);

  // Animate in
  setTimeout(() => {
    toast.style.opacity = "1";
  }, 100);

  // Remove after 3 seconds
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }, 3000);
}

// Search functionality
function initializeSearch() {
  const searchInput = document.querySelector(".search-input");
  if (searchInput) {
    let searchTimeout;

    searchInput.addEventListener("input", function () {
      clearTimeout(searchTimeout);
      const query = this.value.trim();

      if (query.length > 2) {
        searchTimeout = setTimeout(() => {
          performSearch(query);
        }, 300);
      }
    });
  }
}

function performSearch(query) {
  fetch(`/api/users/search?q=${encodeURIComponent(query)}`)
    .then((response) => response.json())
    .then((data) => {
      showSearchResults(data.users);
    })
    .catch((error) => console.error("Search error:", error));
}

function showSearchResults(users) {
  // Implementation for showing search dropdown results
  console.log("Search results:", users);
}
