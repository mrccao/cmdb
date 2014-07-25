$('.modal').on('shown.bs.modal', function() {
    var model_id = $(this).attr("model-id");
    var model_name = $(this).attr("model-name");
    var get_url = "/dependencies/" + model_name + "/" + model_id;
    var body = $(this).find(".modal-body");
    body.empty();
    body.append("<div id='loading'><img src='/static/img/loading.gif' /> Calculating Dependencies</div>");
    dependencies = $.ajax({
        type: "GET",
        dataType: "json",
        url: get_url,
        async: false
    }).responseText;
    var results = JSON.parse(dependencies).results;
    $("div#loading").remove();
    if ( results.length > 0 ) {
        var title = $(this).find(".modal-title");
        console.log(title);
        title.empty();
        title.append("<span class='glyphicon glyphicon-thumbs-down'></span> Dependency Check Failed");
        body.append("<div class='panel panel-danger'><div class='panel-heading'><h3 class='panel-title'>Dependencies</h3></div></div>");
        body.find(".panel").append("<div class='panel-body '>This item cannot be deleted until all dependencies are removed</div>");
        body.find(".panel").append("<table class='table table-hover table-striped table-condensed'><thead><tr class='text-primary'><th>CI</th><th>Name</th></tr></thead><tbody class='rowlink' data-link='row'></tbody></table>");
        var tbody = body.find("tbody");
        for (var i = 0; i < results.length; i++) {
            var id = results[i][0];
            var name = "<td>" + results[i][1] + "</td>";
            var model = results[i][2];
            var friendy_name = "<td><a href='/view/" + model.toLowerCase() + "/?jump=" + id + "'>" + results[i][3] + "</a></td>";
            var row = "<tr>" + friendy_name + name + "</tr>";
            tbody.append(row);
        }
    } else {
        body.append("<h5>No Dependencies</h5>");
        $(this).find(".modal-footer").find("a.btn").removeClass("disabled");
    }
});
