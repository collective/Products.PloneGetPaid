jQuery(function($) {

    /* ship_same_billing enables/disables all inputs of #mailing-address */
    $("#form\\.ship_same_billing").bind('click', function(e) {
        if ($(this).attr('checked')) {
            $("#mailing-address input").attr("disabled", "disabled");
            $("#mailing-address select").attr("disabled", "disabled");
        }
        else {
            $("#mailing-address input").removeAttr("disabled");
            $("#mailing-address select").removeAttr("disabled");
        }
    });

});
