'use strict';
{
    // Sidebar open/close
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

    // Section collapse 
    const currentPathname = window.location.pathname;
    let activePanel = null;

    document.querySelectorAll('.btn-toggle').forEach(button => {
        const targetSelector = button.getAttribute('data-collapse-target');
        const panel = document.querySelector(targetSelector);
        if (!panel) return;

        // Check each link in this section against the current URL
        let isCurrentSection = false;
        panel.querySelectorAll('.sidebar-nav-link').forEach(link => {
            try {
                const linkPath = new URL(link.href).pathname;
                const pattern = new RegExp(`^${linkPath}(/\\d+)?(/add/|/change/|/delete/|/)?$`);
                if (pattern.test(currentPathname) || currentPathname.startsWith(linkPath)) {
                    link.classList.add('selected');
                    isCurrentSection = true;
                }
            } catch (_) { /* skip invalid hrefs */ }
        });

        if (isCurrentSection) {
            panel.classList.add('show');
            button.setAttribute('aria-expanded', 'true');
            activePanel = panel;
        } else {
            panel.classList.remove('show');
            button.setAttribute('aria-expanded', 'false');
        }

        // Click handler — toggle this section, collapse all others
        button.addEventListener('click', () => {
            const isOpen = panel.classList.contains('show');

            // Collapse everything first
            document.querySelectorAll('.collapse_nav.show').forEach(openPanel => {
                openPanel.classList.remove('show');
                const openBtn = document.querySelector(`[data-collapse-target="#${openPanel.id}"]`);
                if (openBtn) openBtn.setAttribute('aria-expanded', 'false');
            });

            // Then open this one if it was closed
            if (!isOpen) {
                panel.classList.add('show');
                button.setAttribute('aria-expanded', 'true');
            }
        });
    });

    // Sidebar quick-filter
    function initSidebarQuickFilter() {
        const searchInput = document.getElementById('sidebar-search-input');
        if (!searchInput || !navSidebar) return;

        // Restore previous session value
        const stored = sessionStorage.getItem('django.admin.navSidebarFilterValue') || '';
        if (stored) {
            searchInput.value = stored;
            applyFilter(stored);
        }

        searchInput.addEventListener('input', () => {
            const value = searchInput.value;
            applyFilter(value);
            sessionStorage.setItem('django.admin.navSidebarFilterValue', value);
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                applyFilter('');
                sessionStorage.removeItem('django.admin.navSidebarFilterValue');
            }
        });
    }

    function applyFilter(filterValue) {
        const searchInput = document.getElementById('sidebar-search-input');
        const lower = filterValue.toLowerCase().trim();
        let anyMatch = false;

        navSidebar.querySelectorAll('.sidebar-section').forEach(sectionLi => {
            const button = sectionLi.querySelector('.btn-toggle');
            const links = sectionLi.querySelectorAll('.sidebar-nav-link');
            let sectionHasMatch = false;

            // Check individual links
            links.forEach(link => {
                const matches = !lower || link.textContent.toLowerCase().includes(lower);
                link.closest('li').style.display = matches ? '' : 'none';
                if (matches) sectionHasMatch = true;
            });

            // If header text matches, show all links in this section
            if (!sectionHasMatch && button) {
                const headerText = button.textContent.toLowerCase();
                if (!lower || headerText.includes(lower)) {
                    sectionHasMatch = true;
                    links.forEach(link => { link.closest('li').style.display = ''; });
                }
            }

            sectionLi.style.display = sectionHasMatch ? '' : 'none';

            // Auto-expand matching sections while filtering
            if (lower && sectionHasMatch) {
                const targetSelector = button ? button.getAttribute('data-collapse-target') : null;
                if (targetSelector) {
                    const panel = document.querySelector(targetSelector);
                    if (panel) panel.classList.add('show');
                }
            }

            if (sectionHasMatch) anyMatch = true;
        });

        // Show/hide zone headers based on whether any section beneath is visible
        navSidebar.querySelectorAll('.sidebar-zone-header').forEach(zoneHeader => {
            let next = zoneHeader.nextElementSibling;
            let zoneVisible = false;
            while (next && !next.classList.contains('sidebar-zone-header') && !next.classList.contains('sidebar-zone-divider')) {
                if (next.style.display !== 'none') zoneVisible = true;
                next = next.nextElementSibling;
            }
            zoneHeader.style.display = (zoneVisible || !lower) ? '' : 'none';
        });

        // Restore collapsed state when filter is cleared
        if (!lower && activePanel) {
            document.querySelectorAll('.collapse_nav').forEach(p => {
                if (p !== activePanel) p.classList.remove('show');
            });
            activePanel.classList.add('show');
        }

        if (searchInput) {
            searchInput.classList.toggle('no-results', !!lower && !anyMatch);
        }
    }

    window.initSidebarQuickFilter = initSidebarQuickFilter;
    initSidebarQuickFilter();
}
