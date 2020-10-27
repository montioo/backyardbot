
// const el = document.getElementById("plugin_empty_field");
// el.innerHTML = "js was here";


class TimetablePlugin extends BybPluginInterface {

    constructor() {
        super();
        this.name = document.getElementById("timetable_plugin_name").innerHTML;
        console.log("constructor of", this.name);

        bybConnection.register_plugin(this);
    }

    receive_data(data) {
        const table = document.getElementById("ttp_table");
        for (var element of data) {
            const table_row = this.create_table_row(element);
            table.appendChild(table_row);
        }
    }

    create_table_row(row_data) {
        const rd = row_data;
        // TODO: Add data-id attribute to identify the table row with the database.
        const row_node = document.createElement("tr");
        for (var attr of [rd["time"], rd["channel"], Math.floor(rd["duration"]/60)]) {
            const cell = document.createElement("td");
            cell.className = "tv_elem";
            cell.appendChild(document.createTextNode(attr));
            row_node.appendChild(cell);
        }
        const cell = document.createElement("td");
        cell.className = "td_remove tv_elem";
        cell.appendChild(document.createTextNode("x"));
        row_node.appendChild(cell);

        // Setting onclick up in html will give the row object, but setting it up in js gives an event.
        const delete_row_callback_wrapper = function(event) {
            // unpacking the calling object from the event.
            this.delete_row(event.target);
        }
        row_node.onclick = delete_row_callback_wrapper.bind(this);

        return row_node;
    }

    delete_row(row_td_obj) {
        // const row_tr_obj = event.target.parentElement;
        const row_tr_obj = row_td_obj.parentElement;
        console.log(row_tr_obj);
        console.log(this.name);
    }
}


// fills a select element with numbers of a given range
function build_selector (start, end, selected, append_to_str) {
    var append_to_elem = document.getElementById(append_to_str);
    var i;
    for (i = start; i <= end; i++)  {
        var option = document.createElement("option");
        var text = "";
        if (i <= 9) {
            text = "0"+i;
        } else {
            text = i;
        }
        if (i == selected) {
            option.setAttribute("selected", "selected");
        }
        option.setAttribute("value", text);
        option.innerHTML = text;
        append_to_elem.appendChild(option);
    }
}

const tt_plugin = new TimetablePlugin();