function getXMLHttpRequest() {
    if (window.XMLHttpRequest){
        ret = new XMLHttpRequest();
    }else if (window.ActiveXObject){
        ret = new ActiveXObject("Microsoft.XMLHTTP");
    }
    return ret;
}

function get_states_from_country(field, field_suffix, dep_suffix, required){
    var req = getXMLHttpRequest()
    var country = field.options[field.selectedIndex].value;
    var url = "@@states-ajax?country=" + country + "&required=" + required;
    req.open("GET", url, true);
    req.onreadystatechange = function(){
                                 update_callback(req, field.id, field_suffix, dep_suffix);
                             };
    req.send(null);
}

function update_sequence(field_id, field_suffix, dep_suffix, response){
    var dep_field_id = field_id.substr(0, field_id.length - field_suffix.length) + dep_suffix;
    var dep_container = document.getElementById(dep_field_id  + "_container");
    var dep_field = document.getElementById(dep_field_id);
    //var dep_value = (dep_field.selectedIndex >= 0) ? dep_field.options[dep_field.selectedIndex].value : '';

    var state_options = "<select name=\"" + dep_field_id + "\" id=\"" + dep_field_id + "\">";
    for (var i = 0; i < response.length; i++){
        //if (dep_value == response[i][0]){
        if (dep_field.selectedIndex == i){
            state_options += "<option value=\"" + response[i][0] + "\" selected>" + response[i][1] + "</option>\n";
        }else{
            state_options += "<option value=\"" + response[i][0] + "\">" + response[i][1] + "</option>\n";
        }
    }
    state_options += "</select>";

    dep_container.innerHTML = state_options;
}

function update_callback(req, field_id, field_suffix, dep_suffix){
   if (req.readyState == 4){
        var response = req.responseText;
        response = eval(response);
        update_sequence(field_id, field_suffix, dep_suffix, response);
    }
}

