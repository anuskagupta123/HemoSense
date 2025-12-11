// Flask/static/js/main.js
document.addEventListener("DOMContentLoaded", function () {

  // AUTH tabs (if page has them)
  const tabLogin = document.getElementById("tabLogin");
  const tabRegister = document.getElementById("tabRegister");
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");

  if (tabLogin && tabRegister) {
    tabLogin.addEventListener("click", () => {
      tabLogin.classList.add("active");
      tabRegister.classList.remove("active");
      loginForm.classList.remove("hidden");
      registerForm.classList.add("hidden");
    });
    tabRegister.addEventListener("click", () => {
      tabRegister.classList.add("active");
      tabLogin.classList.remove("active");
      registerForm.classList.remove("hidden");
      loginForm.classList.add("hidden");
    });
  }

  // theme toggle persistence (light only here - placeholder)
  const themeToggleButtons = document.querySelectorAll(".theme-toggle");
  themeToggleButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      document.body.classList.toggle("dark");
    });
  });

});
