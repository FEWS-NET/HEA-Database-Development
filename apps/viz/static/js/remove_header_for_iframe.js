let isInIframe = (window.location != window.parent.location);
if(isInIframe) {
    let header = $('#header');
    $('body').css('padding', 5);
    header.remove();
    $('.navbar.navbar-default').remove();
}