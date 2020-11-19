
class SprinklerInterfacePlugin extends BybPluginInterface {

    constructor() {
        super();
        this.name = document.getElementById("sprinkler_interface_plugin_name").innerHTML;
        bybConnection.register_plugin(this);
        // this.register();

        this.watering_state_div_id = "sip_watering_state_label";
        this.duration_input_field_id = "sip_duration_input_field";
        this.zone_picker_id = "sip_select_zone";
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

    send_new_watering_cmd() {
        const picked_zone = document.getElementById(this.zone_picker_id).value;
        const duration = document.getElementById(this.duration_input_field_id).value;

        const cmd = {
            command: "start_watering",
            payload: {
                zone: picked_zone,
                duration: duration
            }
        };
        bybConnection.send_to_backend(cmd, this);
        // this.send_to_backend(cmd);
    }
}


const si_plugin = new SprinklerInterfacePlugin();