

class DebugPlugin extends BybPluginInterface {

    constructor() {
        super();
        this.name = document.getElementById("debug_plugin_name").innerHTML;

        bybConnection.register_plugin(this);
    }

    receive_data(data) {
        console.log("received:", data);
    }

    send_json() {
        console.log("btn pressed");
        // const textfiled_plugin_name = document.getElementById("dbp_textfield_plugin_name");
        const textarea_payload = document.getElementById("dbp_textarea_payload");
        const textfiled_receiving_plugin = document.getElementById("dbp_textfield_receiving_plugin");

        const plugin_name = "debug";
        const payload = JSON.parse(textarea_payload.value);
        const destination = document.getElementById("dbp_select_target").value;
        const receiving_plugin = textfiled_receiving_plugin.value;

        const dataframe = JSON.stringify({
            "plugin_name": plugin_name,
            "payload": payload,
            "message_destination": destination,
            "receiving_plugin": receiving_plugin
        })

        console.log(dataframe);
        bybConnection.ws.send(dataframe);
    }
}


var dbp = new DebugPlugin();