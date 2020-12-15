//
// timecontrol.js
// backyardbot
//
// Created: November 2020
// Author: Marius Montebaur
// montebaur.tech, github.com/montioo
//


class TimecontrolPlugin extends BybPluginInterface {

    constructor() {
        super();

        this.time_day_div_id = "tcp_time_day_scheduled";
        this.zones_durations_div_id = "tcp_zones_durations_scheduled";
        this.toggle_auto_btn_id = "tcp_toggle_auto_btn";
        this.skip_next_div_id = "tcp_skip_next_div";

        this.name = document.getElementById("time_control_plugin_name").innerHTML;
        console.log("constructing", this.name);

        bybConnection.register_plugin(this);
    }

    receive_data(data) {
        if (data.constructor != Object || !("command" in data) || !("payload" in data)) {
            // data is not a dict
            console.log("received data that is not a dict:", data);
            return;
        }

        if (data["command"] == "plugin_state") {
            this.display_updated_plugin_state(data["payload"]);
        }
    }

    display_updated_plugin_state(data) {
        console.log("updating plugin content", data);

        const time_day_div = document.getElementById(this.time_day_div_id);
        const zones_durations_div = document.getElementById(this.zones_durations_div_id);
        const skip_next_div = document.getElementById(this.skip_next_div_id);

        const auto_state = data["auto_state"];

        var auto_desc_idx = + !auto_state;  // bool to int, the js way
        document.getElementById(this.toggle_auto_btn_id).innerHTML = tcp_auto_titles[auto_desc_idx];

        const next_time_day = data["next_time_day"];
        time_day_div.innerHTML = next_time_day;

        if (auto_state) {
            const next_zone_duration = data["next_zone_duration"];
            zones_durations_div.innerHTML = next_zone_duration;
            zones_durations_div.style.display = "";
            skip_next_div.style.display = "";
        } else {
            zones_durations_div.style.display = "none";
            skip_next_div.style.display = "none";
        }
    }

    skip_watering_btn() {
        console.log("skip next watering");

        const cmd = {
            command: "skip_next_watering",
            payload: null
        };
        bybConnection.send_to_backend(cmd, this);
    }

    toggle_auto_mode_btn(sender) {
        const target_state = Boolean(tcp_auto_titles.indexOf(sender.innerHTML));

        const cmd = {
            command: "toggle_auto_mode",
            payload: target_state
        };
        bybConnection.send_to_backend(cmd, this);
    }
}


const tc_plugin = new TimecontrolPlugin();

