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
let running_job = null

function get_container() {
    $.getJSON("/container", function (data) {
        if (JSON.stringify(data) !== JSON.stringify(container)) {
            container = data
            console.log("container", container)
            select = $("#FormUnitSelect")
            crane = $("#crane-details-container")
            select.empty()
            for (id in container) {
                if (container[id].stack === "crane") {
                    crane.text("Container: " + container[id].number)
                } else {
                    crane.text("Container: none")
                }
                select.append($("<option></option>").attr("value", id).text(container[id].number + " [" + container[id].stack + "]"))
            }
            select.append($("<option></option>").attr("value", -1).text(""))
            update_stack_table()
        }
    })
}

function get_stacks() {
    $.getJSON("/stacks", function (data) {
        if (JSON.stringify(data) !== JSON.stringify(stacks)) {
            stacks = data
            console.log("stacks", stacks)
            select = $("#FormTargetSelect")
            select.empty()
            for (id in stacks) {
                space = stacks[id].height - stacks[id].container.length
                select.append($("<option></option>").attr("value", id).text(stacks[id].name + " [" + stacks[id].container.length + "]" + " [" + space + "]"))
            }
            update_stack_table()
        }
    })
}

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

function get_crane_container() {
    for (id in container) {
        if (container[id].stack === "crane") {
            return container[id].number
        }
    }
    return ""
}

function get_crane_container_id() {
    for (id in container) {
        if (container[id].stack === "crane") {
            return id
        }
    }
    return ""
}

function update_stack_table(url, element_id = "output") {
    $.ajax({
        url: "ajax_stack_table",
        success: function (data) {
            document.getElementById("stack_table").innerHTML = data;
        }

    });
}

function update_stack_table_obs() {
    return
    stacks_table = $("#stacks table tbody")
    stacks_table_head = $("#stacks table thead")
    stacks_table.empty()
    stacks_table_head.empty()
    crane_container = get_crane_container()

    stacks_table_head.append('<tr style="font-size: 14px;" class="table-dark"></tr>')
    last = stacks_table_head.children("tr:last")
    for (id in stacks) {
        last.append("<td>" + stacks[id].name + "</td>")
    }
    last.append("<td>crane</td>")

    indexes = [2, 1, 0]
    for (idx in indexes) {
        stacks_table.append("<tr></tr>")

        last = stacks_table.children("tr:last")
        for (ids in stacks) {
            if (stacks[ids].container.length > indexes[idx]) {
                last.append("<td class='bg-secondary'>" + stacks[ids].container[indexes[idx]].number + "</td>")
            } else {
                last.append("<td>-</td>")
            }
        }
        if (indexes[idx] === 0) {
            if (crane_container === "") {
                last.append("<td>-</td>")
            } else {
                last.append("<td class='bg-danger'>" + crane_container + "</td>")
            }
        } else {
            last.append("<td>-</td>")
        }
    }

    stacks_table.append('<tr></tr>')
    last = stacks_table.children("tr:last")
    for (id in stacks) {
        last.append('<td class="text-center">' + stacks[id].coordinates.x + "/" + stacks[id].coordinates.y + "/" + stacks[id].coordinates.z + "</td>")
    }
    last.append("<td></td>")

    stacks_table.append("<tr></tr>")
    last = stacks_table.children("tr:last")
    for (id in stacks) {
        last.append('<td class="text-center"><button data-stack-name="' + stacks[id].name + '" style="font-size: 10px" type="button" class="btn btn-primary set-pos ">set pos</button></td>')
    }
    last.append("<td></td>")

    $(".set-pos").click(function () {
        stack_name = $(this).attr("data-stack-name");
        console.log(stack_name);
        data = {
            "x": pos_x,
            "y": pos_y,
            "z": pos_z,
        }
        console.log(data);
        $.ajax({
            url: "stacks/setpos/" + stack_name,
            type: "POST",
            data: JSON.stringify(data),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (data) {
                console.log(data)
            }
        })
    });
}

function set_form() {
    const unitselect = $("#FormUnitSelect")
    const targetSelect = $("#FormTargetSelect")
    const targetSelected = $("#FormTargetSelect option:selected")
    const typeSelectMove = $("#type-select-move")
    const typeSelectDrop = $("#type-select-drop")
    const typeSelectPick = $("#type-select-pick")
    const typeSelect = $("#FormTypeSelect")
    const targetX = $("#FormTargetX")
    const targetY = $("#FormTargetY")
    const targetZ = $("#FormTargetZ")
    unitselect.prop('disabled', "disabled");
    if (get_crane_container_id() === "") {
        if (typeSelect.val() === "drop"){
            typeSelect.val("pick")
        }
        typeSelectDrop.attr('disabled', 'disabled');
        typeSelectPick.removeAttr('disabled');
    } else {
        if (typeSelect.val() === "pick"){
            typeSelect.val("drop")
        }
        typeSelectPick.attr('disabled', 'disabled');
        typeSelectDrop.removeAttr('disabled');
    }
    if (typeSelect.val() === "move") {
        targetX.parent().show()
        targetY.parent().show()
        targetZ.parent().show()
        unitselect.parent().hide()
        targetSelect.parent().hide()
        //targetX.val($("#crane_position").text())
        //targetY.val($("#katz_position").text())
        //targetZ.val($("#spreader_position").text())
    } else {
        targetX.parent().hide()
        targetY.parent().hide()
        targetZ.parent().hide()
        unitselect.parent().show()
        targetSelect.parent().show()
        if (typeSelect.val() === "drop") {
            // Todo
            unitselect.val(get_crane_container_id())
        } else {
            const target_stack = stacks[targetSelected.val()]
            if (target_stack !== undefined) {
                if(target_stack.container[target_stack.container.length -1] === undefined){
                    unitselect.val(-1)
                }else {
                    for (id in container) {
                        if (container[id].number === target_stack.container[target_stack.container.length -1].number) {
                            unitselect.val(id)
                            break
                        }
                    }
                }
            }

        }
    }
}

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
    get_container()
    get_stacks()

    setInterval(function () {
        get_messages()
    }, 500);

    setInterval(function () {
        get_job()
        get_container()
        get_stacks()
        get_metrics()
        set_form()
    }, 1000);

    $(".not-clickable").on("click", false);

    $('#FormTypeSelect').on('change', function () {
        set_form()
    });

    $('#FormTargetSelect').on('change', function () {
        set_form()
    });

    $("#cancel-job").click(function () {
        cancel_job()
    })

    $("#send-job").click(function () {
        send_job()
    })
});
