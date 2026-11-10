// Shared by every signed-in page: fills in "Welcome <name>!" from the server.
fetch("/api/me")
  .then((response) => (response.ok ? response.json() : Promise.reject()))
  .then((me) => {
    document.getElementById("welcome").textContent = `Welcome ${me.name}!`;
  })
  .catch(() => {
    window.location.href = "/";   // session expired or signed out in another tab
  });
