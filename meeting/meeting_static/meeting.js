document.addEventListener("DOMContentLoaded", () => {

  // -----------------------------
  // Sidebar toggle y links activos
  // -----------------------------
  const sidebarToggler = document.getElementById("sidebar-toggler");
  const sidebar = document.getElementById("sidebar");
  const content = document.getElementById("main-content");

  if (sidebarToggler) {
    sidebarToggler.addEventListener("click", () => {
      sidebar.classList.toggle("active");
      if (window.innerWidth >= 992 && content) {
        content.classList.toggle("shifted"); // Ajusta contenido cuando sidebar se expande
      }
    });
  }

  // Marcar link activo en sidebar
  const menuLinks = document.querySelectorAll(".sidebar-menu a");
  const currentPath = window.location.pathname.split("/").pop();

  menuLinks.forEach(link => {
    const linkPath = link.getAttribute("href");
    if (linkPath === currentPath) {
      link.classList.add("active");
      const parentCollapse = link.closest(".collapse");
      if (parentCollapse) {
        parentCollapse.classList.add("show");
        const parentTrigger = document.querySelector(`[href="#${parentCollapse.id}"]`);
        if (parentTrigger) parentTrigger.setAttribute("aria-expanded", "true");
      }
    }
  });

  // -----------------------------
  // Flatpickr (si existe campo fecha)
  // -----------------------------
  if (document.querySelector("#fecha")) {
    flatpickr("#fecha", {
      dateFormat: "d-m-Y",
      locale: "es"
    });
  }


});
