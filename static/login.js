const form = document.getElementById("login-form");
const error = document.getElementById("error");

form.addEventListener("submit", async (event) => {
  event.preventDefault();   // stop the browser's own form submit; we send JSON ourselves
  error.textContent = "";

  let response;
  try {
    response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: form.username.value, password: form.password.value }),
    });
  } catch {
    error.textContent = "Can't reach the server. Is app.py running?";
    return;
  }

  const data = await response.json();
  if (!response.ok) {
    error.textContent = data.error;
    form.password.value = "";
    form.password.focus();
    return;
  }
  window.location.href = data.home;   // the server says where this role belongs
});
