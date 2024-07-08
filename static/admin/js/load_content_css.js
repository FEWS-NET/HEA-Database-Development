// The content div and the object-tools are shared between different pages as they are inherited from
// a parent template. In order to provide different look and feel based on the fdw design, we need to
// allocate classes and styling dynamically based on the page from which they are rendered
document.addEventListener("DOMContentLoaded", function() {
    let loc = window.location.toString();
    let content = document.getElementById("content");
    let objectTools = document.querySelector(".object-tools");
    
    // For making background light gray if the page is other than home
    let reg = new RegExp("/admin/[A-Za-z]*/$");
    if (reg.test(loc) || loc.endsWith("/admin/")) {
        content.classList.remove("content_with_background");
    } else {
        content.classList.add("content_with_background");
    }

    // For adjusting the margin for change pages
    if (loc.includes("/change/")) {
        objectTools.classList.add("object-tools-top-margin");
    } else {
        let actionsDiv = document.querySelector(".actions");
        let toolbarDiv = document.getElementById("toolbar");
        
        if (actionsDiv) {
            objectTools.classList.remove("object-tools-top-margin");
            actionsDiv.appendChild(objectTools);
            objectTools.classList.add("object-tools-top-margin-list-page");
        } else if (toolbarDiv) {
            objectTools.classList.remove("object-tools-top-margin");
            toolbarDiv.appendChild(objectTools);
            objectTools.classList.add("object-tools-top-margin-list-page");
        } else {
            let titlePageDiv = document.getElementById("title-page-div");
            if (objectTools != null){
            objectTools.classList.remove("object-tools-top-margin");
            titlePageDiv.appendChild(objectTools);
            objectTools.classList.add("object-tools-top-margin-no-action-search-bar");
            }
        }
    }
});
