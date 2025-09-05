// ==========================================================
// Spinal Tumor Detection - script.js (FULL & CORRECTED with Validation)
// ==========================================================
// Add this new function at the top of your script.js file

function initializeGoogleSignIn() {
  google.accounts.id.initialize({
    client_id: "556631616994-pul2e57kp0oblfsddj3uslophlrc9v5a.apps.googleusercontent.com",
    callback: handleGoogleCredentialResponse // The function that handles the login response
  });
}
// Global variables
let predictionsChart = null;
let profileManager; // Will be initialized on DOMContentLoaded

// ---------- Small helpers ----------
const getToken = () => (localStorage.getItem("token") || "").trim();

async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", "Bearer " + token);

  return fetch(url, {
    ...options,
    headers,
    mode: "cors",            // ✅ enforce CORS
    credentials: "include"   // ✅ required since backend uses supports_credentials=True
  });
}


function handleUnauthorized(res) {
  if (res.status === 401 || res.status === 403) {
    alert("Your session has expired or is invalid. Please sign in again.");
    localStorage.removeItem("token");
    window.location.reload();
    return true;
  }
  return false;
}

async function handleGoogleCredentialResponse(response) {
  console.log("Encoded JWT ID token: " + response.credential);

  // Send the token to your backend
  try {
    const res = await fetch("https://spinalcord-tumor.onrender.com/api/auth/google-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: response.credential })
    });

    const data = await res.json();

    if (res.ok) {
      // If backend login is successful, save our own app's token and user info
      localStorage.setItem("token", data.token);
      localStorage.setItem("username", data.user.name);
      localStorage.setItem("email", data.user.email);

      // Find the showAppView function to transition to the main app
      // This assumes showAppView is accessible in the global scope or defined earlier
      const mainAppLoader = document.querySelector('body[data-show-app-view]');
      if (mainAppLoader) {
          window[mainAppLoader.dataset.showAppView]();
      } else {
          // Fallback if the above method isn't set up: just reload
          window.location.reload();
      }

    } else {
      // If the backend returned an error
      alert(data.msg || "Google login failed on the server.");
    }
  } catch (error) {
    console.error("Error sending Google token to backend:", error);
    alert("Could not connect to the server for Google Sign-In.");
  }
}

// ---------- Chatbot ----------
function toggleChat() {
  const box = document.getElementById("chatbox");
  box.style.display = box.style.display === "flex" ? "none" : "flex";
}

function handleKeyPress(event) {
  if (event.key === "Enter") processInput();
}

async function processInput() {
  const userInput = document.getElementById("userInput");
  const query = userInput.value.trim();
  if (!query) return;

  const userId = localStorage.getItem("username") || "guest";
  addMessage("user", query);
  userInput.value = "";

  try {
    const response = await authFetch("https://spinalcord-tumor.onrender.com/api/chatbot/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId, question: query })
    });

    if (!response.ok) {
      if (handleUnauthorized(response)) return;
      throw new Error("Server error");
    }

    const data = await response.json();
    addMessage("bot", data.answer);
  } catch (error) {
    console.error("Chatbot API error:", error);
    addMessage("bot", "Sorry, I'm having trouble connecting.");
  }
}

function addMessage(sender, text) {
  const chat = document.getElementById("chat-content");
  const msg = document.createElement("div");
  msg.className = sender === "user" ? "chat-user" : "chat-bot";
  msg.innerHTML = text;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

// ---------- Dashboard & Analytics ----------
async function updateDashboard() {
  const token = getToken();
  if (!token) {
    alert("Please log in again.");
    window.location.reload();
    return;
  }

  try {
    const res = await authFetch("https://spinalcord-tumor.onrender.com/api/predict/stats", {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });

    if (!res.ok) {
      if (handleUnauthorized(res)) return;
      throw new Error(`Failed to fetch stats: ${res.status}`);
    }

    const data = await res.json();

    // Update the recent predictions table
    const tableBody = document.getElementById("predictions-table-body");
    tableBody.innerHTML = "";
    if (!data.recent_predictions || data.recent_predictions.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="4">No predictions made yet.</td></tr>';
    } else {
      data.recent_predictions.forEach((pred) => {
        const row = document.createElement("tr");
        const resultClass =
          pred.result === "Tumor Detected" ? "result-tumor" : "result-no-tumor";
        row.innerHTML = `
          <td>${pred.date}</td>
          <td>${pred.filename}</td>
          <td class="${resultClass}">${pred.result}</td>
          <td>${pred.confidence}</td>
        `;
        tableBody.appendChild(row);
      });
    }

    // Update the summary chart
    const ctx = document.getElementById("predictionsChart").getContext("2d");
    const chartData = {
      labels: ["Tumor Detected", "No Tumor"],
      datasets: [
        {
          label: "Prediction Count",
          data: [data.total_counts.tumor, data.total_counts.no_tumor],
          backgroundColor: ["rgba(255, 99, 132, 0.5)", "rgba(75, 192, 192, 0.5)"],
          borderColor: ["rgba(255, 99, 132, 1)", "rgba(75, 192, 192, 1)"],
          borderWidth: 1
        }
      ]
    };

    if (predictionsChart) {
      predictionsChart.data = chartData;
      predictionsChart.update();
    } else {
      predictionsChart = new Chart(ctx, {
        type: "bar",
        data: chartData,
        options: {
          scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
          responsive: true,
          maintainAspectRatio: false
        }
      });
    }
  } catch (error) {
    console.error("❌ Could not update dashboard:", error);
    document.getElementById("predictions-table-body").innerHTML =
      '<tr><td colspan="4">Error loading data.</td></tr>';
  }
}

// **IMPROVEMENT**: This new function calls the Profile Manager
// It replaces the old, redundant function
async function loadUserProfile() {
    if (profileManager) {
        await profileManager.loadData();
    }
}

// ---------- Chat History ----------
async function loadChatHistory() {
  const userId = localStorage.getItem("username") || "guest";
  try {
    const res = await authFetch("https://spinalcord-tumor.onrender.com/api/chatbot/history", {
      method: "GET"
    });

    if (!res.ok) {
      if (handleUnauthorized(res)) return;
      throw new Error("Failed to fetch chat history");
    }

    const history = await res.json();
    const tableBody = document.getElementById("chatbot-history-table-body");
    if (!tableBody) return;

    tableBody.innerHTML = "";
    if (history.length === 0) {
      tableBody.innerHTML = "<tr><td colspan='3'>No chat history found.</td></tr>";
    } else {
      history.forEach((chat) => {
        const row = `
          <tr>
            <td>${chat.timestamp}</td>
            <td>${chat.question}</td>
            <td>${chat.answer}</td>
          </tr>
        `;
        tableBody.innerHTML += row;
      });
    }
  } catch (err) {
    console.error("Failed to load chat history", err);
    const tableBody = document.getElementById("chatbot-history-table-body");
    if (tableBody) {
      tableBody.innerHTML =
        "<tr><td colspan='3'>Error loading chat history.</td></tr>";
    }
  }
}

// ---------- Page Navigation & Theme ----------
function showPage(pageId, element) {
  document.querySelectorAll(".page").forEach((page) => page.classList.remove("active"));
  const targetPage = document.getElementById(pageId);
  if (targetPage) targetPage.classList.add("active");

  document
    .querySelectorAll(".sidebar a")
    .forEach((link) => link.classList.remove("active"));
  if (element) element.classList.add("active");
  
  // Slider fix
  if (pageId === 'home-dashboard') {
      try {
        $('#home-dashboard .slider').slick('setPosition');
      } catch (e) {
        console.error("Could not reposition Slick slider:", e);
      }
  }

  if (pageId === "dashboard-page") updateDashboard();
  if (pageId === "profile-page") {
    loadUserProfile();
    loadChatHistory();
  }
}

function toggleTheme() {
  document.body.classList.toggle("dark-mode");
  const btn = document.getElementById("theme-toggle");
  btn.textContent = document.body.classList.contains("dark-mode")
    ? "☀️ Light Mode"
    : "🌙 Dark Mode";
}

// ---------- Slick Carousel ----------
(function initSlickIfPresent() {
  if (window.$ && typeof $(".slider")?.slick === "function") {
    $(document).ready(function () {
      $(".slider").slick({
        autoplay: true,
        autoplaySpeed: 2500,
        dots: false,
        arrows: false,
        fade: true
      });
    });
  }
})();

// ---------- Main (on DOMContentLoaded) ----------
document.addEventListener("DOMContentLoaded", () => {
  // **IMPROVEMENT**: Initialize the profile manager for the whole app
  profileManager = new ProfilePhotoManager();

  const loginPage = document.getElementById("login-page");
  const logoutButtonTop = document.getElementById("logoutButtonTop");
  const logoutButtonSidebar = document.getElementById("logoutButtonSidebar");
  const signUpButton = document.getElementById("signUp");
  const signInButton = document.getElementById("signIn");
  const container = document.getElementById("container");
  const authMessage = document.getElementById("auth-message");
  const signUpForm = document.getElementById("signUpForm");
  const signInForm = document.getElementById("signInForm");
  const predictButton = document.getElementById("predictButton");
  const mriFileInput = document.getElementById("mriFileInput");
  const predictionResult = document.getElementById("predictionResult");
  const imagePreviewContainer = document.getElementById("image-preview-container");
  const imagePreview = document.getElementById("image-preview");
  const clearButton = document.getElementById("clear-button");
  const dropZone = document.getElementById("drop-zone");
  const loader = document.getElementById("loader");
  const downloadPdfButton = document.getElementById("downloadPdfButton");
  let currentFile = null;

  // View management
  const showAppView = () => {
    document.getElementById("login-page").style.display = "none";
    document.body.classList.add("sidebar-active");
    const name = localStorage.getItem("username") || "";
    const nameDisplay = document.getElementById("user-name-display");
    if (nameDisplay) nameDisplay.textContent = name;
    
    document.querySelector('body').dataset.showAppView = 'showAppView';

    showPage("home-dashboard", document.querySelector(".sidebar a"));
  };

  const showLoginView = () => {
    document.getElementById("login-page").style.display = "block";
    document.body.classList.remove("sidebar-active");
  };

  // Auth helpers
  const showAuthMessage = (message, isError = false) => {
    authMessage.textContent = message;
    authMessage.className = "auth-message-box";
    authMessage.classList.add(isError ? "error" : "success");
    authMessage.style.display = "block";
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("email");
    localStorage.removeItem("predictionHistory");
    window.location.reload();
  };

  // --- START: NEW & CORRECTED CODE FOR GOOGLE BUTTONS ---
  const googleSignInBtn = document.getElementById('googleSignInBtn');
  const googleSignUpBtn = document.getElementById('googleSignUpBtn');

  const handleGoogleLogin = (e) => {
    e.preventDefault(); // Stop the link from trying to navigate

    if (window.google && window.google.accounts && window.google.accounts.id) {
      // This function will show the Google One Tap or pop-up
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          console.warn("Google Sign-In prompt was not displayed.");
        }
      });
    } else {
      console.error("Google Identity Services script has not loaded yet.");
      alert("Google Sign-In is not ready. Please try again in a moment.");
    }
  };

  googleSignInBtn?.addEventListener('click', handleGoogleLogin);
  googleSignUpBtn?.addEventListener('click', handleGoogleLogin);
  // --- END: NEW & CORRECTED CODE ---

  if (container) {
    signUpButton?.addEventListener("click", () =>
      container.classList.add("right-panel-active")
    );
    signInButton?.addEventListener("click", () =>
      container.classList.remove("right-panel-active")
    );
  }
  logoutButtonTop?.addEventListener("click", handleLogout);
  logoutButtonSidebar?.addEventListener("click", handleLogout);

  // Sign-Up
  signUpForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("signUpName").value;
    const email = document.getElementById("signUpEmail").value;
    const password = document.getElementById("signUpPassword").value;

    try {
      const res = await fetch("https://spinalcord-tumor.onrender.com/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
      });
      const data = await res.json();
      if (res.ok) {
        showAuthMessage("Registration successful! Please sign in.");
        container.classList.remove("right-panel-active");
      } else {
        showAuthMessage(data.msg || "Registration failed.", true);
      }
    } catch (error) {
      showAuthMessage("Could not connect to server.", true);
    }
  });

  // Sign-In
  signInForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("signInEmail").value;
    const password = document.getElementById("signInPassword").value;
    try {
      const res = await fetch("https://spinalcord-tumor.onrender.com/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("username", data.user.name);
        localStorage.setItem("email", data.user.email);
        showAppView();
      } else {
        showAuthMessage(data.msg || "Login failed.", true);
      }
    } catch (error) {
      showAuthMessage("Could not connect to server.", true);
    }
  });

  // File Upload & Preview
  const handleFile = (file) => {
    if (!file) return;

    const allowedExtensions = /(\.jpg|\.jpeg|\.png)$/i;
    if (!allowedExtensions.exec(file.name)) {
        predictionResult.textContent = "Warning: For best results, please upload a standard image file (JPG, PNG).";
        predictionResult.className = "result error";
    } else if (!file.type.startsWith("image/")) {
        predictionResult.textContent = "Invalid file type. Please select a valid image.";
        predictionResult.className = "result error";
        mriFileInput.value = "";
        return;
    } else {
        predictionResult.textContent = "Upload an image to see the prediction.";
        predictionResult.className = "result";
    }
    
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      imagePreviewContainer.style.display = "block";
      dropZone.style.display = "none";
    };
    reader.readAsDataURL(file);
  };

  const resetUploader = () => {
    currentFile = null;
    mriFileInput.value = "";
    imagePreviewContainer.style.display = "none";
    dropZone.style.display = "block";
    predictionResult.textContent = "Upload an image to see the prediction.";
    predictionResult.className = "result";
    downloadPdfButton.style.display = "none";
  };

  dropZone?.addEventListener("click", () => mriFileInput.click());
  mriFileInput?.addEventListener("change", (e) => handleFile(e.target.files[0]));
  dropZone?.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone?.addEventListener("dragleave", () =>
    dropZone.classList.remove("drag-over")
  );
  dropZone?.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    handleFile(e.dataTransfer.files[0]);
  });
  clearButton?.addEventListener("click", resetUploader);

  // Prediction (Upload)
  predictButton?.addEventListener("click", async () => {
    if (!currentFile) {
      predictionResult.textContent = "Please select a file first.";
      predictionResult.className = "result error";
      return;
    }
    loader.style.display = "block";
    predictButton.disabled = true;
    predictionResult.textContent = "Analyzing...";
    predictionResult.className = "result";
    downloadPdfButton.style.display = "none";

    const formData = new FormData();
    formData.append("mriScan", currentFile);

    try {
      const res = await authFetch("https://spinalcord-tumor.onrender.com/api/predict/upload", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (res.ok) {
        predictionResult.textContent = `Prediction: ${data.prediction.result} (Confidence: ${data.prediction.confidence})`;
        predictionResult.className = `result ${
          data.prediction.result === "Tumor Detected" ? "positive" : "negative"
        }`;
        downloadPdfButton.style.display = "block";

        const history = JSON.parse(localStorage.getItem("predictionHistory")) || [];
        history.unshift({
          filename: currentFile.name,
          result: data.prediction.result,
          confidence: data.prediction.confidence,
          date: new Date().toLocaleString()
        });
        localStorage.setItem("predictionHistory", JSON.stringify(history.slice(0, 20)));
      
      } else {
        if (handleUnauthorized(res)) return;
        
        if (data.msg && data.msg.includes("Validation Error")) {
            predictionResult.textContent = data.msg;
        } else {
            predictionResult.textContent = `Error: ${data.msg || "Prediction failed."}`;
        }
        predictionResult.className = "result error";
      }
    } catch (error) {
      predictionResult.textContent = "Error: Could not connect to the server.";
      predictionResult.className = "result error";
    } finally {
      loader.style.display = "none";
      predictButton.disabled = false;
    }
  });
  
  // Download PDF
  downloadPdfButton?.addEventListener("click", function () {
    const { jsPDF } = window.jspdf || {};
    if (!jsPDF) {
      alert("PDF library not loaded.");
      return;
    }

    const doc = new jsPDF();
    const userName = localStorage.getItem("username") || "N/A";
    const predictionText = document.getElementById("predictionResult").innerText;
    const imgElement = document.getElementById("image-preview");
    const currentDate = new Date().toLocaleString();
    const reportId = "REP-" + Date.now();

    doc.setFontSize(18);
    doc.setFont("helvetica", "bold");
    doc.text("Spinal Tumor Detection Report", 105, 20, null, null, "center");
    doc.setFontSize(12);
    doc.setFont("helvetica", "normal");
    doc.text(`Patient Name: ${userName}`, 14, 40);
    doc.text(`Report ID: ${reportId}`, 14, 47);
    doc.text(`Date: ${currentDate}`, 14, 54);
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text("Uploaded MRI Scan:", 14, 70);
    if (imgElement && imgElement.src && imgElement.src.startsWith("data:image")) {
      doc.addImage(imgElement.src, "JPEG", 14, 75, 80, 80);
    }
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text("Prediction Analysis:", 14, 165);
    doc.setFontSize(12);
    doc.setFont("helvetica", "normal");
    if (predictionText.includes("Tumor Detected")) {
      doc.setTextColor(200, 0, 0);
    } else {
      doc.setTextColor(0, 150, 0);
    }
    doc.text(predictionText, 14, 172);
    doc.setTextColor(0, 0, 0);
    const history = JSON.parse(localStorage.getItem("predictionHistory")) || [];
    if (history.length > 0) {
      const rows = history.map((pred) => [
        pred.filename,
        pred.result,
        pred.confidence,
        pred.date
      ]);
      if (doc.autoTable) {
        doc.autoTable({
          head: [["Filename", "Prediction", "Confidence", "Date"]],
          body: rows,
          startY: 185,
          styles: { fontSize: 11, cellPadding: 3 },
          headStyles: { fillColor: [41, 128, 185], textColor: 255 }
        });
      }
    }
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(
      "Disclaimer: This report is generated by an AI model and should be reviewed by a medical professional.",
      14,
      285
    );
    doc.save(`Spinal_Tumor_Report_${reportId}.pdf`);
  });

  // Initialize view
  if (getToken()) {
    showAppView();
  } else {
    showLoginView();
  }
});

// ---------- Profile Tabs Switching ----------
document.querySelectorAll(".tab-link").forEach((button) => {
  button.addEventListener("click", () => {
    const tabId = button.getAttribute("data-tab");

    document.querySelectorAll(".tab-pane").forEach((pane) => {
      pane.classList.remove("active");
    });
    document.querySelectorAll(".tab-link").forEach((btn) => {
      btn.classList.remove("active");
    });

    document.getElementById(tabId).classList.add("active");
    button.classList.add("active");

    if (tabId === "chat-history") {
      loadChatHistory();
    }
  });
});


// **IMPROVEMENT**: Fully integrated ProfilePhotoManager class
class ProfilePhotoManager {
  constructor() {
    this.profilePictureInput = document.getElementById('profilePictureInput');
    this.profilePicture = document.getElementById('profilePicture');
    this.profileDetailsForm = document.getElementById('profile-details-form');
    this.currentUserEmail = null;
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    if (this.profilePictureInput) {
      this.profilePictureInput.addEventListener('change', (e) => this.handlePhotoUpload(e));
    }
    if (this.profileDetailsForm) {
      this.profileDetailsForm.addEventListener('submit', (e) => this.handleProfileUpdate(e));
    }
  }

  async loadData() {
    try {
      const userEmail = localStorage.getItem('email');
      if (!userEmail) {
          console.error("No user email found in localStorage.");
          return;
      }
      this.currentUserEmail = userEmail;
      
      const response = await authFetch(`https://spinalcord-tumor.onrender.com/api/profile/${userEmail}`);
      
      if (response.ok) {
        const userData = await response.json();
        this.populateUserData(userData);
      } else {
          console.error('Failed to load user profile data from server. Falling back to localStorage.');
          this.populateUserData({
              name: localStorage.getItem("username"),
              email: localStorage.getItem("email"),
              profilePhoto: null
          });
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
      this.showMessage('Error loading profile data', 'error');
    }
  }

  populateUserData(userData) {
    const defaultPic = 'user.jpg';
    if (this.profilePicture) {
        this.profilePicture.src = userData.profilePhoto || defaultPic;
    }
    
    const nameField = document.getElementById('profileName');
    const emailField = document.getElementById('profileEmail');
    const headerName = document.getElementById('profileHeaderName');
    const headerEmail = document.getElementById('profileHeaderEmail');
    
    if (nameField) nameField.value = userData.name || '';
    if (emailField) emailField.value = userData.email || '';
    if (headerName) headerName.textContent = userData.name || 'User Name';
    if (headerEmail) headerEmail.textContent = userData.email || 'user@example.com';
  }

  async handlePhotoUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      this.showMessage('File size must be less than 5MB', 'error');
      return;
    }
    if (!file.type.startsWith('image/')) {
      this.showMessage('Please select a valid image file', 'error');
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      if (this.profilePicture) {
        this.profilePicture.src = e.target.result;
      }
    };
    reader.readAsDataURL(file);
    
    await this.uploadPhotoToServer(file);
  }

  async uploadPhotoToServer(file) {
    try {
      this.showMessage('Uploading photo...', 'info');
      const formData = new FormData();
      formData.append('profilePicture', file);
      formData.append('userEmail', this.currentUserEmail);

      const response = await authFetch('https://spinalcord-tumor.onrender.com/api/profile/upload-photo', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      if (response.ok && result.success) {
        this.showMessage('Profile picture updated successfully!', 'success');
        if (this.profilePicture) {
          this.profilePicture.src = result.photoUrl;
        }
      } else {
        this.showMessage(result.error || 'Upload failed', 'error');
      }
    } catch (error) {
      console.error('Photo upload error:', error);
      this.showMessage('Network error during upload', 'error');
    }
  }

  async handleProfileUpdate(event) {
    event.preventDefault();
    const nameField = document.getElementById('profileName');
    if (!nameField) return;
    
    const updateData = {
      name: nameField.value,
      currentUserEmail: this.currentUserEmail
    };
    
    try {
      this.showMessage('Updating profile...', 'info');
      const response = await authFetch('https://spinalcord-tumor.onrender.com/api/profile/update', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });
      
      const result = await response.json();
      if (response.ok && result.success) {
        this.showMessage('Profile updated successfully!', 'success');
        
        localStorage.setItem('username', updateData.name);
        
        const headerName = document.getElementById('profileHeaderName');
        const welcomeName = document.getElementById('user-name-display');
        
        if (headerName) headerName.textContent = updateData.name;
        if (welcomeName) welcomeName.textContent = updateData.name;

      } else {
        this.showMessage(result.error || 'Update failed', 'error');
      }
    } catch (error) {
      console.error('Profile update error:', error);
      this.showMessage('Network error during update', 'error');
    }
  }

  showMessage(message, type) {
    let messageDiv = document.getElementById('profile-message');
    if (!messageDiv) {
      messageDiv = document.createElement('div');
      messageDiv.id = 'profile-message';
      messageDiv.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 15px 20px;
        border-radius: 5px; color: white; font-weight: bold; z-index: 10000;
        max-width: 300px; word-wrap: break-word;`;
      document.body.appendChild(messageDiv);
    }
    const colors = { success: '#28a745', error: '#dc3545', info: '#17a2b8' };
    messageDiv.style.backgroundColor = colors[type] || colors.info;
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
    setTimeout(() => {
      if (messageDiv) {
        messageDiv.style.display = 'none';
      }
    }, 4000);
  }
}
