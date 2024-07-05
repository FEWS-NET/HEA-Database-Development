'use strict';
{
    const toggleNavSidebar = document.getElementById('toggle-nav-sidebar');
    const navSidebar = document.getElementById('nav-sidebar');
    const main = document.getElementById('main');
    let navSidebarIsOpen = localStorage.getItem('django.admin.navSidebarIsOpen') === 'true';
    if (toggleNavSidebar !== null) {
        main.classList.toggle('shifted', navSidebarIsOpen);
        navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);

        toggleNavSidebar.addEventListener('click', function() {
            navSidebarIsOpen = !navSidebarIsOpen;
            localStorage.setItem('django.admin.navSidebarIsOpen', navSidebarIsOpen);
            main.classList.toggle('shifted');
            navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);
        });
    }

    const currentUrl = window.location.href;
    let selectedElement = null;

    document.querySelectorAll('.btn-toggle').forEach(button => {
        const target = button.getAttribute('data-bs-target');
        const targetElement = document.querySelector(target);
        let isCurrentLink = false;

        document.querySelectorAll('.btn-toggle-nav a').forEach(link => {
            const linkUrl = new URL(link.href);
            const pattern = new RegExp(`^${linkUrl.pathname}(/\\d+)?(/add/|/change/|/delete/|/)?$`);
            if (pattern.test(currentUrl) || currentUrl.startsWith(link.href)) {
                link.classList.add('selected');
                if (link.closest('.collapse') === targetElement) {
                    isCurrentLink = true;
                }
            }
        });

        if (isCurrentLink) {
            button.setAttribute('aria-expanded', 'true');
            targetElement.classList.add('show');
            selectedElement = targetElement;
        } else {
            button.setAttribute('aria-expanded', 'false');
            targetElement.classList.remove('show');
        }

        button.addEventListener('click', () => {
            const expanded = button.getAttribute('aria-expanded') === 'true';
            button.setAttribute('aria-expanded', !expanded);
            targetElement.classList.toggle('show');
        });
    });

    if (selectedElement) {
        document.querySelectorAll('.collapse').forEach(element => {
            if (element !== selectedElement) {
                element.classList.remove('show');
                element.previousElementSibling.setAttribute('aria-expanded', 'false');
            }
        });
    }

    function initSidebarQuickFilter() {
        const options = [];
        if (!navSidebar) {
            return;
        }
        navSidebar.querySelectorAll('th[scope=row] a').forEach((container) => {
            options.push({title: container.innerHTML, node: container});
        });

        function checkValue(event) {
            let filterValue = event.target.value.toLowerCase();
            if (event.key === 'Escape') {
                filterValue = '';
                event.target.value = ''; // clear input
            }
            let matches = false;
            for (const o of options) {
                let displayValue = '';
                if (filterValue && o.title.toLowerCase().indexOf(filterValue) === -1) {
                    displayValue = 'none';
                } else {
                    matches = true;
                }
                o.node.parentNode.parentNode.style.display = displayValue;
            }
            if (!filterValue || matches) {
                event.target.classList.remove('no-results');
            } else {
                event.target.classList.add('no-results');
            }
            sessionStorage.setItem('django.admin.navSidebarFilterValue', filterValue);
        }
    }

    window.initSidebarQuickFilter = initSidebarQuickFilter;
    initSidebarQuickFilter();
}
