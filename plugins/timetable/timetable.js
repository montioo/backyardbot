//
// timetable.js
// backyardbot
//
// Created: October 2020
// Author: Marius Montebaur
// montebaur.tech, github.com/montioo
//


function int_list_to_string(int_list) {
    // s = str(l)  <- python <3
    var s = "";
    for (var v of int_list) {
        s += v.toString() + ", ";
    }
    return s.slice(0, s.length - 2);
}

function toStringZeroPadding(n, digit_count) {
    var s = n.toString();
    // jeez is that ugly
    while (s.length < digit_count) s = "0" + s;
    return s;
}


class TimetablePlugin extends BybPluginInterface {

    constructor() {
        super();
        this.name = document.getElementById("timetable_plugin_name").innerHTML;
        console.log("constructor of", this.name);
        this.overlay_id = "ttp_new_element_overlay";

        bybConnection.register_plugin(this);
    }

    receive_data(data) {
        if (data.constructor != Object || !("command" in data) || !("payload" in data)) {
            // data is not a dict
            console.log("received data that is not a dict:", data);
            return;
        }

        const action_dict = {
            "timetable_contents": this.display_updated_timetable
            // more message handlers ...
        };

        // action_dict[data["command"]](data["payload"]);

        if (data["command"] == "timetable_contents") {
            this.display_updated_timetable(data["payload"]);
        }
    }

    display_updated_timetable(data) {
        // receives an updated timetable list from the backend and displays it.
        const table = document.getElementById("ttp_table");
        const tbody = table.getElementsByTagName("tbody")[0];
        // TODO: Do not delete the header
        // clear table (but keep header)
        while (tbody.children.length > 1) {
            tbody.removeChild(tbody.lastChild);
        }

        var last_weekday = -1;
        for (var element of data) {
            if (element.weekday != last_weekday) {
                // tbody.appendChild(this.create_table_divider(element.weekday.toString()))
                tbody.appendChild(this.create_table_divider(element.weekday.toString()))
                last_weekday = element.weekday;
            }
            const table_row = this.create_table_row(element);
            tbody.appendChild(table_row);
        }
    }

    create_table_divider(weekday_str) {
        var tr = document.createElement("tr");

        var td = document.createElement("td");
        td.setAttribute("colspan", "4");
        td.style.paddingLeft = "20px";
        // TODO: Add safety for when parseInt fails.
        const weekday_index = parseInt(weekday_str);
        if (weekday_index == 7) {
            td.innerHTML = tt_plugin_daily;
        } else {
            td.innerHTML = tt_plugin_weekdays[weekday_index];
        }
        tr.appendChild(td);
        tr.className = "tv_day";
        return tr;
    }

    create_table_row(row_data) {
        // row_data: Dict with elements:
        //     "time_hh": Int,
        //     "time_mm": Int,
        //     "duration": Int,    // seconds
        //     "weekday": Int,     // Mon = 0, ...  <=!! only a scalar
        //     "zones": [Str],     // watering zones
        //     "doc_id": Int       // unique id from DB
        // The frontend receives table data with only a scalar for the weekday for better visualization.

        var dur_string = "";
        const units = [[Math.floor(row_data["duration"]/60), "\u202Fmin"], [row_data["duration"]%60, "\u202Fsec"]];
        for (var unit of units) {
            if (unit[0] > 0) {
                if (dur_string.length > 0) { dur_string += ", "; }
                dur_string += unit[0].toString() + unit[1];
            }
        }

        // TODO: Only show if it's not 0 and the same for sec.
        const row_vals = [
            toStringZeroPadding(row_data["time_hh"], 2) + ":" + toStringZeroPadding(row_data["time_mm"], 2),
            int_list_to_string(row_data["zones"]),
            dur_string,
            "\u00D7"  // unicode multiplication sign
        ];

        // TODO: Add data-id attribute to identify the table row with the database.
        const row_node = document.createElement("tr");
        row_node.dataset.doc_id = row_data["doc_id"];
        var cell;
        for (var cell_content of row_vals) {
            cell = document.createElement("td");
            cell.className = "tv_elem";
            cell.appendChild(document.createTextNode(cell_content));
            row_node.appendChild(cell);
        }
        cell.classList.add("td_remove");

        // Setting onclick up in html will give the row object, but setting it up in js gives an event.
        const delete_row_callback_wrapper = function(event) {
            // unpacking the calling object from the event.
            this.delete_row(event.target);
        }
        // row_node.onclick = delete_row_callback_wrapper.bind(this);
        cell.onclick = delete_row_callback_wrapper.bind(this);

        return row_node;
    }

    delete_row(row_td_obj) {
        // const row_tr_obj = event.target.parentElement;
        const row_tr_obj = row_td_obj.parentElement;
        const doc_id_to_del = row_tr_obj.dataset.doc_id;
        const cmd = {
            "command": "remove_entry",
            "payload": parseInt(doc_id_to_del)
        };
        bybConnection.send_to_backend(cmd, this);
    }

    show_overlay() {
        show_overlay(this.overlay_id);
    }

    remove_overlay(sender) {
        show_overlay(this.overlay_id);
    }

    overlay_add_pressed() {
        // row_data: Dict with elements:
        //     "time_hh": Int,
        //     "time_mm": Int,
        //     "duration": Int,    // seconds
        //     "weekday": Int,     // Mon = 0, ...
        //     "zones": [Int],     // watering zones
        //     "doc_id": Int       // unique id from DB

        const entries = this.parse_from_overlay();
        if (entries == null) { return }

        // reset error from previous attempts
        this.overlay_error_visible(false);
        // TODO: Reset overlay contents

        // This is the new element that will be added to the DB.
        // After adding this, the server will broadcast the updated DB to all clients.
        const cmd = {
            "command": "add_entries",
            "payload": entries
        };

        bybConnection.send_to_backend(cmd, this);
    }

    parse_from_overlay() {
        const overlay = document.getElementById(this.overlay_id);

        var entry_data = {};

        const time_field = document.getElementById("ttp_time_input_field");
        const duration_field = document.getElementById("ttp_duration_input_field");
        if ((time_field.value.length == 0) && (duration_field.value.length == 0)) {
            this.overlay_error_visible(true);
            return null;
        }

        // "time_hh": Int, "time_mm": Int,
        entry_data["time_hh"] = parseInt(time_field.value.slice(0, 2));
        entry_data["time_mm"] = parseInt(time_field.value.slice(3, 5));

        // "weekdays": [Int],  // Mon = 0, ...
        const wd_parent_id = "ttp_day_selector";
        const data_id = "weekdays";
        entry_data[data_id] = [];
        for (var child_idx = 0; child_idx < document.getElementById(wd_parent_id).children.length; child_idx++) {
            const selection_div = document.getElementById(wd_parent_id).children[child_idx];
            if (selection_div.classList.contains("selector_box_selected")) {
                entry_data[data_id].push(child_idx);
            }
        }

        // "zone": [str]       // watering zones
        const parent_id = "ttp_channel_selector";
        entry_data["zones"] = [];
        for (var child_idx = 0; child_idx < document.getElementById(parent_id).children.length; child_idx++) {
            const selection_div = document.getElementById(parent_id).children[child_idx];
            if (selection_div.classList.contains("selector_box_selected")) {
                entry_data["zones"].push(selection_div.innerHTML);
            }
        }

        for (var el of ["zones", "weekdays"]) {
            if (entry_data[el].length == 0) {
                console.log("not enough", el);
                this.overlay_error_visible(true);
                return null;
            }
        }

        // "duration": Int,    // seconds
        const duration_mins = parseInt(duration_field.value.slice(0, 2));
        const duration_secs = parseInt(duration_field.value.slice(3, 5));
        entry_data["duration"] = 60*duration_mins + duration_secs;

        hide_overlay(this.overlay_id);

        var weekdays_list = [];
        // split entries: create an entry for each weekday
        if (entry_data["weekdays"].length == 7) {
            // water at all days
            weekdays_list.push(7);
        } else {
            weekdays_list = entry_data["weekdays"];
        }

        var entries = [];
        for (var day_id of weekdays_list) {
            entries.push({
                time_hh: entry_data["time_hh"],
                time_mm: entry_data["time_mm"],
                weekday: day_id,
                zones: entry_data["zones"],
                duration: entry_data["duration"]
            })
        }

        return entries;
    }

    overlay_error_visible(is_visible) {
        const error_div = document.getElementById("ttp_overlay_error_msg");
        error_div.style.display = (is_visible) ? "block" : "none";
    }
}


const tt_plugin = new TimetablePlugin();

