
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
        const row_node = document.createElement("tr");
        for (var attr of ["time", "channel", "duration"]) {
            const cell = document.createElement("td");
            cell.className = "tv_elem";
            cell.appendChild(document.createTextNode(row_data[attr]));
            row_node.appendChild(cell);
        }
        const cell = document.createElement("td");
        cell.className = "td_remove tv_elem";
        cell.appendChild(document.createTextNode("x"));
        row_node.appendChild(cell);
        return row_node;
    }
}


const tt_plugin = new TimetablePlugin();