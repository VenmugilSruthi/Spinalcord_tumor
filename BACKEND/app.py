// Example: Save token after login
async function loginUser(email, password) {
  const response = await fetch("https://spinalcord-tumor.onrender.com/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();
  if (response.ok) {
    localStorage.setItem("token", data.token); // save JWT
    alert("Login successful!");
  } else {
    alert(data.msg || "Login failed");
  }
}

// Upload MRI scan with token
async function uploadMRI(file) {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("Please log in first!");
    return;
  }

  const formData = new FormData();
  formData.append("mriScan", file);

  const response = await fetch("https://spinalcord-tumor.onrender.com/api/predict/upload", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + token  # ✅ attach token

    },
    body: formData
  });

  const data = await response.json();
  if (response.ok) {
    console.log("Prediction:", data);
    alert("Result: " + data.prediction.result + " | Confidence: " + data.prediction.confidence);
  } else {
    alert("Error: " + (data.msg || "Upload failed"));
  }
}
