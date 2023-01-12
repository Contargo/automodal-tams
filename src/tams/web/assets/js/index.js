function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function event() {
    return {
        type: "net.contargo.logistics.tams.TBD",
        site: "terminal",
        timestamp: new Date().toISOString(),
        version: "v1",
        producer: "ccs.automodal.contargo.net",
        location: "DEKOB",
        guid: uuidv4(),
    }
}

let container = []
let stacks = []
let pos_x = 0
let pos_y = 0
let pos_z = 0

function get_details() {
    $.getJSON("/details", function (data) {
        console.log("details", data)
        if (data["features"].length !== 0) {
            feature_list = $("#feature-list")
            feature_list.empty()
            for (id in data["features"]) {
                type = data["features"][id].type
                version = data["features"][id].version
                feature_list.append($("<li></li>").text(type + " " + version))
            }
        }
    })
}

function get_messages() {
    $.getJSON("/messages", function (data) {
        if (data["msg"].length !== 0) {
            for (msg in data["msg"]) {
                color = "<span>"
                if (data["msg"][msg].type !== "OK") {
                    color = '<span class="text-danger">'
                }
                $("#messages-console").prepend(
                    color + '$> <b>' + data["msg"][msg].title + ':</b> ' + data["msg"][msg].text + '</span><br>'
                );
            }
        }
    })
}

function get_metrics() {
    $.getJSON("/metric", function (data) {
        //console.log(data)
        if ("metrics" in data && data["metrics"].length !== 0) {
            //console.log(data["metrics"])
            for (id in data["metrics"]) {
                if (data["metrics"][id].name === "CraneCoordinatesX") {
                    $("#crane_position").text(data["metrics"][id].value)
                    pos_x = data["metrics"][id].value
                }
                if (data["metrics"][id].name === "CraneCoordinatesY") {
                    $("#katz_position").text(data["metrics"][id].value)
                    pos_y = data["metrics"][id].value
                }
                if (data["metrics"][id].name === "CraneCoordinatesZ") {
                    $("#spreader_position").text(data["metrics"][id].value)
                    pos_z = data["metrics"][id].value
                }
                if (data["metrics"][id].name === "StatusPowerOn") {
                    $("#crane-status-power").prop('checked', data["metrics"][id].value);
                }

                if (data["metrics"][id].name === "StatusManuelMode") {
                    $("#crane-status-manual").prop('checked', data["metrics"][id].value);
                }

                if (data["metrics"][id].name === "StatusAutomaticMode") {
                    $("#crane-status-automatic").prop('checked', data["metrics"][id].value);
                }
                if (data["metrics"][id].name === "StatusSandFusion") {
                    $("#fusion-status").prop('checked', data["metrics"][id].value);
                }
                if (data["metrics"][id].name === "JobCancel") {
                    $("#job-cancel-status").prop('checked', data["metrics"][id].value);
                }
            }
        }
    })
}

function get_job() {
    $.getJSON("/job", function (data) {
        jobcard = $("#running-job")
        //console.log("JOB:", data)
        jobcard.empty()
        if ($.isEmptyObject(data)) {
            jobcard.append("<ul>" +
                "<li><b>type:</b> </li>" +
                "<li><b>x:</b>  </li>" +
                "<li><b>y:</b>  </li>" +
                "<li><b>z:</b>  </li>" +
                "<li><b>unit nr:</b>  </li>" +
                "<li><b>unit id:</b>  </li>" +
                "<li><b>unit type:</b> </li>" +
                "</ul>")
        } else {
            jobcard.append("<ul>" +
                "<li><b>type:</b> " + data.type + "</li>" +
                "<li><b>x:</b> " + data.target.x + "</li>" +
                "<li><b>y:</b> " + data.target.y + "</li>" +
                "<li><b>z:</b> " + data.target.z + "</li>" +
                "<li><b>unit nr:</b> " + data.unit.number + "</li>" +
                "<li><b>unit id:</b> " + data.unit.unit_id + "</li>" +
                "<li><b>unit type:</b> " + data.unit.type + "</li>" +
                "</ul>")
        }
    })
}


function update_stack_table() {
    $.ajax({
        url: "ajax_stack_table",
        type: "GET",
        success: function (data) {
            document.getElementById("stack_table").innerHTML = data;
            $(".set-pos").on('click', function (event) {
                event.stopPropagation();
                event.stopImmediatePropagation();
                stack_name = $(this).attr("data-stack-name");
                console.log(stack_name);
                data = {
                    "x": pos_x,
                    "y": pos_y,
                    "z": pos_z,
                }
                console.log(data);
                setpos_event.data = data
                $.ajax({
                    url: "stacks/setpos/" + stack_name,
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (data) {
                        console.log(data)
                        document.dispatchEvent(update_ui_event);
                    },
                    error: function (data) {
                        console.log("failed")
                        document.dispatchEvent(update_ui_event);
                    }
                })

            });
            $(".drop-container").on('click', function (event) {
                stack_name = $(this).attr("data-stack-name");
                stack_layer= $(this).attr("data-stack-layer");
                $.ajax({
                    url: "stacks/drop/" + stack_name + "/" + stack_layer,
                    type: "POST",
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (data) {
                        console.log(data)
                        document.dispatchEvent(update_ui_event);
                    },
                    error: function (data) {
                        console.log("failed")
                        document.dispatchEvent(update_ui_event);
                    }
                })
            });
            $('.stacks_init').on('change', function (event) {
                event.stopPropagation();
                event.stopImmediatePropagation();
                stack_name = $(this).attr("data-stack-name");
                layer = $(this).attr("data-layer");
                container = $(this).children("option:selected").text().replace(" ","_")
                url = "stacks/container/" + layer + "/" + stack_name + "/" + container
                console.log("url: " + url)
                $.ajax({
                    url: url,
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (data) {
                        console.log("OK")
                        document.dispatchEvent(update_ui_event);
                    },
                    error: function (data) {
                        console.log("failed")
                        document.dispatchEvent(update_ui_event);
                    }
                })
            });
            $('#move-container-button').on('click', function () {
                from = $("#move-container-from").children("option:selected").text()
                to = $("#move-container-to").children("option:selected").text()
                console.log(from)
                console.log(to)
                $.ajax({
                    url: "container/generate_move/" + from + "/" + to,
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (data) {
                        console.log(data)
                        document.dispatchEvent(update_ui_event);
                    },
                    error: function (data) {
                        console.log("failed")
                        document.dispatchEvent(update_ui_event);
                    }
                })
            });
        }

    });


}

function update_auto_job() {
    $.ajax({
        url: "ajax_auto_job",
        type: "GET",
        success: function (data) {
            document.getElementById("auto_job").innerHTML = data;
        }

    });
}

function update_job_status() {
    $.ajax({
        url: "ajax_job_status",
        type: "GET",
        success: function (data) {
            document.getElementById("job_status").innerHTML = data;
        }

    });
}

function update_crane_status() {
    $.ajax({
        url: "ajax_crane_status",
        type: "GET",
        success: function (data) {
            document.getElementById("crane_status").innerHTML = data;
        }

    });
}

function update_job_list() {
    $.ajax({
        url: "ajax_job_list",
        type: "GET",
        success: function (data) {
            document.getElementById("job_list").innerHTML = data;
        }

    });
}

document.addEventListener("update_ui", function(e) {
    update_job_list()
    update_stack_table()
    update_auto_job()
    update_job_status()
    update_crane_status()
});

var update_ui_event = new CustomEvent("update_ui", { "detail": "Example of an event" });
var setpos_event = new CustomEvent("setpos", { "detail": "Example of an event" });

function send_job() {
    const unitform = $("#FormUnitSelect option:selected")
    const targetform = $("#FormTargetSelect option:selected")
    const unit = container[unitform.val()]
    const target = stacks[targetform.val()]
    let coordinates = target.coordinates
    const type = $("#FormTypeSelect option:selected").val()
    if (unit.number !== unitform.text()) {
        console.log("SEND JOB FAILED unit.number !== unitform.text()")
        console.log(unit.number, unitform.text())
    }

    if (type !== "move") {
        console.log(typeof coordinates.z, coordinates.z)
        console.log("target stack:", target)
        // correct height by container cound in stack
        // 2,591m height default iso container
        if (type === "pick") {
            coordinates.z = coordinates.z + (target.container.length - 1) * 2591 - 200
        }else{ // drop
            coordinates.z = coordinates.z + target.container.length * 2591 - 200
        }
    }
    if (type === "move") {
        coordinates.x = $("#FormTargetX").val()
        coordinates.y = $("#FormTargetY").val()
        coordinates.z = $("#FormTargetZ").val()
    }
    data = {
        "metadata": event(),
        "type": type,
        "target": coordinates, // Coordinaten
        "unit": unit, // CCSUNIT
    }
    console.log("job", data)
    $.ajax({
        url: "job",
        data: JSON.stringify(data),
        type: "POST",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            console.log(data)
        }
    })
}

function cancel_job() {
    $.ajax({
        url: "job_cancel",
        type: "POST",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            console.log(data)
        }
    })
}

$(document).ready(function () {

    $.getJSON("/state", function (data) {
        console.log("state", data)
    })

    get_details()
    //get_container()
    //get_stacks()
    // ajax
    document.dispatchEvent(update_ui_event);
    document.dispatchEvent(setpos_event);


    setInterval(function () {
        get_messages()
    }, 500);

    setInterval(function () {
        get_job()
        //get_container()
        //get_stacks()
        get_metrics()
    }, 1000);

    $(".not-clickable").on("click", false);

    checkbox_modus = $(".checkbox_modus")
    checkbox_modus.prop("checked", false)
    $("#checkbox_modus_init").prop("checked", true)
    checkbox_modus.on('change', function () {
        $(".checkbox_modus").not(this).prop('checked', false)
        $(this).prop('checked', true)
        $.ajax({
            url: "mode",
            data: this.id.split("_")[2],
            type: "POST",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                console.log(data)
                document.dispatchEvent(update_ui_event);
                //update_ui()
            },
            error: function (data) {
                console.log(data)
            }

        });
    });


});
