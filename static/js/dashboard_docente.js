const sidebar = document.getElementById("sidebar");
const toggleButton = document.getElementById("toggleSidebar");

if (sidebar && toggleButton) {
  toggleButton.addEventListener("click", () => sidebar.classList.toggle("active"));
}
