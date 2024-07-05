// To make result_list table row selectable based on the first href assigned to the columns
document.addEventListener("DOMContentLoaded", function (event) {
    var result_list_table = document.getElementById("result_list");
    if (typeof result_list_table !== "undefined" & result_list_table != null) {
        /* Iterate over the cells for each row and find a first anchor tag, the admin usually use the first cell as a link
        / When we find a tags, break to the next row, but a cell may contain more than 1 anchor tags as in the case for
        / Treebeard admin table, in that case we need to use the second tag */
        for (let row of result_list_table.rows) {
            for (let cell of row.cells) {
                let anchors = cell.getElementsByTagName("a"); // all anchor tags for a given cell
                let a ;
                if (anchors.length == 1) {
                    a = anchors[0]
                } else if (anchors.length == 2) { // treebeard has a get_collapse method that adds an anchor to the first cell
                    a = anchors[1]
                }
                if (typeof a != "undefined") {
                    row.addEventListener('click', function (event) {
                        // Only allow the click to be fired from the cell elements, to ignore events from checkbox and header
                        if (String(event.target) == "[object HTMLTableCellElement]") {
                            window.location = a.href;
                        }
                    });
                    break; // we found the first legitimate anchor
                }
            }
        }
    }
});

