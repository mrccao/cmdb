function input_group(selector, icon, append) {
    if(typeof(append)==='undefined') append = false;
    //var append = false;
    var input_group_div = '<div class="input-group"></div>';
    var input_group_addon_div = '<div class="input-group-addon"></div>';
    var icon = '<span class="glyphicon glyphicon-' + icon + '"></span>';
    if (append) {
        selector.wrap(input_group_div).parent().append(input_group_addon_div).children().first().append(icon);
    } else {
        selector.wrap(input_group_div).parent().prepend(input_group_addon_div).children().first().append(icon);
    }
}
