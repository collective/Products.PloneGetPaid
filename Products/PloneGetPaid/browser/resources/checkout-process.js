jQuery(function($) {

    /* ship_same_billing enables/disables all inputs of #mailing-address */
    $("#form\\.ship_same_billing").bind('click', function(e) {

        var $disable = '';
        if ($(this).attr('checked')) {
            $disable = 'disabled';
        }
        $("#mailing-address input").attr("disabled", $disable);
        $("#mailing-address select").attr("disabled", $disable);
        $(this).removeAttr('disabled');
    });

});