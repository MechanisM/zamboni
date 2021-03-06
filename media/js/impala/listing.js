$(function() {
    $('.performance-note .popup').each(function(i,p) {
        var $p = $(this),
            $a = $p.siblings('a').first();
        $p.popup($a, {width: 300, pointTo: $a});
    });

    // Mark incompatible add-ons on listing pages.
    $('.listing .item.addon').each(function(i,p) {
        var $this = $(this);
        if ($this.find('.concealed').length == $this.find('.button').length) {
            $this.addClass('incompatible');
        }
    });

    // Advanced search dropdown.
    $('#sorter').delegate('select', 'change', function() {
        window.location = $('#sorter form').attr('action') + '?sort=' + $(this).val();
    });

    // Make this row appear 'static' so the installation buttons and pop-ups
    // stay open when hovering outside the item row.
    $(document.body).bind('newStatic', function() {
        $('.install-note:visible').closest('.item').addClass('static');
    }).bind('closeStatic', function() {
        $('.item.static').removeClass('static');
    });
});
