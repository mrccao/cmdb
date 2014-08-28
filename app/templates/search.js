function navigate_list(selector, up) {
     if ( $(selector).length ) {
        if ( ! up ) {
            if ( !$(selector).find("tr.info").length ) {
                $(selector).find("tr").first().addClass("info");
            } else if ( $(selector).find("tr.info").closest("tr").is(":last-child") ) {
                $(selector).find("tr").first().addClass("info");
                $(selector).find("tr.info").last().removeClass("info");
            } else {
                $(selector).find("tr.info").next().addClass("info");
                $(selector).find("tr.info").first().removeClass("info");
            }
        } else {
            if ( !$(selector).find("tr.info").length ) {
                $(selector).find("tr").last().addClass("info");
            } else if ( $(selector).find("tr.info").closest("tr").is(":first-child") ) {
                $(selector).find("tr").last().addClass("info");
                $(selector).find("tr.info").first().removeClass("info");
            } else {
                $(selector).find("tr.info").prev().addClass("info");
                $(selector).find("tr.info").last().removeClass("info");
            }
        }
        return true;
    }
    return false;
}

function keyboard_down() {
    if ( navigate_list("#search_results", false))
       return false;
    else if ( navigate_list("#view_results", false))
       return false;
}

function keyboard_up() {
    if ( navigate_list("#search_results", true) )
       return false;
    else if ( navigate_list("#view_results", true) )
       return false;
}

function open_search_result() {
    if ( $("#search_results>tr").length ) {
        $("#search_results").find("tr.info").find("a").click();
        return false;
    } else if ( $("#view_results>tr").length ) {
        $("#view_results").find("tr.info").find("a").click();
        return false;
    }
    return true;
}

function apply_search_shortcuts() {
    var thread = null;
 
    $(document).off('keydown');
    $("#search").off('keydown');
    $("input").off('keydown');

    $(document).on('keydown', null, 'esc', function(){
        $("#search").focus();
    });
    
    $(document).on('keydown', null, 'down', keyboard_down);
    $(document).on('keydown', null, 'up', keyboard_up);
    $(document).on('keydown', null, 'return', open_search_result);

   $('#search').keyup(function() {
        clearTimeout(thread);
        var target = $(this);
        thread = setTimeout(function() { run_search(target.val()); }, 500); 
    });

    $("#search").on('keydown', null, 'return', function(){
        if ( $("#search").val().length < 3 && ! $("#search_results>tr").length  && !$("#view_results").find("tr.info").length ) {
            run_search($("#search").val(), false);
            return false;
        } else {
            return open_search_result();
        }
    });
 
    $("#search").on('keydown', null, 'down', keyboard_down);
    $("#search").on('keydown', null, 'up', keyboard_up);

    $("input, select").on('keydown', null, 'esc', function(){
        if ($("#search").is(":focus")) {
            if ( $("#search").val().length ) {
                $("#search").val("");
            } else {
                location.reload();    
            }
        } else {
            $("#search").focus();
       }
    });
}

function search_skeleton() {
    var table = '<table class="table table-hover table-striped" id="search_result_table">';
    table += '<thead><tr class="lead"><th>CI</th><th>Name</th><th>Matched</th></tr></thead>';
    table += '<tbody data-link="row" class="rowlink" id="search_results"></tbody>';
    table += '</table>';
    return table;
}

function run_search(search_term, check_term) {
    if( check_term === undefined ) check_term = true;
    if ( check_term && search_term.length < 3) {
        return true;
    }
    if (search_term == $("#search").data("search")) {
        return true;
    }
    $("#search").data("search", search_term);
    var loading = "<tr><td><img src='/static/img/loading.gif' /></td></tr>";
    body_selector = $("div.body-container").first();
    if ( !$("#search_result_table").length ) {
        body_selector.empty();
        table = search_skeleton();
        body_selector.append(table);
    }
    $("#search_results").empty();
    $("#search_results").append(loading);
    $.post( "/assets/instant-search/", {search: search_term}, function( data ) {
        $("#search_results").empty();
        $("#search_results").append(data);
        $("#search_results tr:first-child").addClass("info");
        apply_search_shortcuts();
    });
}
    
$('#search').attr('autocomplete', 'off');

$(document).on('click', "tr.info", function() {
    window.open($("#view_results").find("tr.info").find("a").attr("href"), "_self");
});

apply_search_shortcuts();
