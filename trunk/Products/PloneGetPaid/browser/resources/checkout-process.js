function disableMailingAddress() {
    $("#mailing-address input").attr("disabled","disabled"); 
    $("#mailing-address select").attr("disabled","disabled"); 
    $("#form\\.ship_same_billing").attr({onclick: "enableMailingAddress()", disabled: ""})
}

function enableMailingAddress() {
    $("#mailing-address input").attr("disabled",""); 
    $("#mailing-address select").attr("disabled",""); 
    $("#form\\.ship_same_billing").attr("onclick", "disableMailingAddress()")
}
