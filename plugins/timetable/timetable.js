
// const el = document.getElementById("plugin_empty_field");
// el.innerHTML = "js was here";


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
        td.innerHTML = weekday_str;
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
        //     "zones": [Int],     // watering zones
        //     "doc_id": Int       // unique id from DB
        // The frontend receives table data with only a scalar for the weekday for better visualization.

        // TODO: Only show if it's not 0 and the same for sec.
        const row_vals = [
            toStringZeroPadding(row_data["time_hh"], 2) + ":" + toStringZeroPadding(row_data["time_mm"], 2),
            int_list_to_string(row_data["zones"]),
            Math.floor(row_data["duration"]/60).toString() + "min, " + (row_data["duration"]%60).toString() + "sec",
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
        const cmd = { remove_entry: parseInt(doc_id_to_del) };
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

        // This is the new element that will be added to the DB.
        // After adding this, the server will broadcast the updated DB to all clients.
        const cmd = { add_entries: entries };

        bybConnection.send_to_backend(cmd, this);
    }

    parse_from_overlay() {
        const overlay = document.getElementById(this.overlay_id);

        var entry_data = {};

        const time_field = document.getElementById("ttp_time_input_field");
        const duration_field = document.getElementById("ttp_duration_input_field");
        if ((time_field.value.length == 0) && (duration_field.value.length == 0)) {
            this.overlay_error_visible(true);
            return;
        }

        // "time_hh": Int, "time_mm": Int,
        entry_data["time_hh"] = parseInt(time_field.value.slice(0, 2));
        entry_data["time_mm"] = parseInt(time_field.value.slice(3, 5));

        // "weekdays": [Int],  // Mon = 0, ...
        // "zone": [Int]       // watering zones
        const button_list = [["ttp_channel_selector", "zones"], ["ttp_day_selector", "weekdays"]];
        // for (const [parent_id, data_id] of button_list) {
        for (var idx = 0; idx < button_list.length; idx++) {
            const parent_id = button_list[idx][0];
            const data_id = button_list[idx][1];
            entry_data[data_id] = [];
            for (var child_idx = 0; child_idx < document.getElementById(parent_id).children.length; child_idx++) {
                const selection_div = document.getElementById(parent_id).children[child_idx];
                if (selection_div.classList.contains("selector_box_selected")) {
                    entry_data[data_id].push(child_idx);
                }
            }
            if (entry_data[data_id].length == 0) {
                console.log("not enough", data_id);
                this.overlay_error_visible(true);
                return;
            }
        }
        // add 1 to each zone since they are not counted from 0
        entry_data["zones"] = entry_data["zones"].map(x => x+1);

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

