
class SprinklerInterfacePlugin extends BybPluginInterface {

    constructor() {
        super();
        this.name = document.getElementById("sprinkler_interface_plugin_name").innerHTML;
        bybConnection.register_plugin(this);

        this.watering_state_div_id = "sip_watering_state_label";
    }

    receive_data(data) {
        if (data.constructor != Object || !("command" in data) || !("payload" in data)) {
            console.log("sprinkler plugin received invalid data:", data);
            return;
        }

        if (data["command"] == "watering_state") {
            this.display_updated_watering_state(data["payload"]);
        }
    }

    display_updated_watering_state(state_string) {
        const state_field = document.getElementById(this.watering_state_div_id);
        state_field.innerHTML = state_string;
    }
}


const si_plugin = new SprinklerInterfacePlugin();