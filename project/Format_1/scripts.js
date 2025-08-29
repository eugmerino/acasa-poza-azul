document.addEventListener("DOMContentLoaded", () => {
  // Cargar Header y Sidebar dinámicamente
  loadFragment("../Format_1/header.html", "header-placeholder");
  loadFragment("./Format_1/sidebar.html", "sidebar-placeholder");

  function loadFragment(file, placeholderId) {
    fetch(file)
      .then((res) => res.text())
      .then((html) => {
        document.getElementById(placeholderId).innerHTML = html;

        // Re-inicializar eventos después de inyectar el HTML
        if (file.includes("header") || file.includes("sidebar")) {
          initSidebar();
        }
      });
  }

  function initSidebar() {
    const sidebarToggler = document.getElementById("sidebar-toggler");
    const sidebar = document.getElementById("sidebar");
    const content = document.getElementById("main-content");

    if (sidebarToggler) {
      sidebarToggler.addEventListener("click", () => {
        sidebar.classList.toggle("active");
        if (window.innerWidth >= 992 && content) {
          content.classList.toggle("shifted");
        }
      });
    }

    // Marcar link activo
    const menuLinks = document.querySelectorAll(".sidebar-menu a");
    const currentPath = window.location.pathname.split("/").pop();

    menuLinks.forEach((link) => {
      const linkPath = link.getAttribute("href");
      if (
        linkPath === currentPath ||
        (currentPath === "" && linkPath === "inicio.html")
      ) {
        link.classList.add("active");
        const parentCollapse = link.closest(".collapse");
        if (parentCollapse) {
          parentCollapse.classList.add("show");
          const parentTrigger = document.querySelector(
            `[href="#${parentCollapse.id}"]`
          );
          if (parentTrigger) {
            parentTrigger.setAttribute("aria-expanded", "true");
          }
        }
      }
    });
  }

  // Inicializar Flatpickr
  if (document.querySelector("#fecha")) {
    flatpickr("#fecha", { dateFormat: "d-m-Y", locale: "es" });
  }
});

