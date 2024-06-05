document.addEventListener('DOMContentLoaded', function() {
  const search_filter = document.getElementById("filter-search");

  function searchFilter() {
    const links = document.querySelectorAll('#changelist-filter ul li a');
    const searchValue = search_filter.value.toLowerCase();

    // Iterate through all links and display/hide based on search input
    for (let link of links) {
      if (searchValue === '' || link.textContent.toLowerCase().includes(searchValue)) {
        link.parentElement.style.display = 'block';
      } else {
        link.parentElement.style.display = 'none';
      }
    }
  }

  if (search_filter) {
    // Add event listeners for 'keyup' and 'search' events
    search_filter.addEventListener('keyup', searchFilter);
    search_filter.addEventListener('search', searchFilter);
  }
});


