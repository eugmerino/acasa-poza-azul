document.addEventListener("DOMContentLoaded", function () {
      const sidebarToggler = document.getElementById("sidebar-toggler");
      const sidebar = document.getElementById("sidebar");
      const content = document.getElementById("main-content");

      sidebarToggler.addEventListener("click", function () {
        sidebar.classList.toggle("active");

        if (window.innerWidth >= 992) {
          content.classList.toggle("shifted");
        }
      });

      content.addEventListener("click", function () {
        if (window.innerWidth < 992) {
          sidebar.classList.remove("active");
        }
      });

    });

    // Oculta el sidebar si la pantalla es menor a 992px
    function handleSidebarOnResize() {
      const sidebar = document.getElementById('sidebar');
      if (window.innerWidth < 992) {
        sidebar.classList.remove('active');
      }
    }
    window.addEventListener('DOMContentLoaded', handleSidebarOnResize);
    window.addEventListener('resize', handleSidebarOnResize);