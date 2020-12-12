//
// sprinklerinterface.js
// backyardbot
//
// Created: December 2020
// Author: Marius Montebaur
// montebaur.tech, github.com/montioo
//


class ZoneDisplayTimer {
    // Constructs a timer that will count down a number of seconds an update its
    // time as a string in a html tag with a certain id. The id is randomly
    // generated when the object is created and it's the responsibility of the
    // code that initializes the timer to create an object with the
    // corresponding id.

    constructor(start_time_sec) {
        this.time_content_div_id = this.make_id(8);
        this.remaining_time = start_time_sec;

        // Bind the method like this to make `this` refer to the class instance
        this.timer = setInterval(this.update_displayed_time.bind(this), 1000);
    }

    update_displayed_time() {
        // Normally when called by setInterval, `this` will refer to window.
        // Circumvent by binding `this` to the class instance.

        this.remaining_time -= 1;
        const timer_div = document.getElementById(this.time_content_div_id);
        if (timer_div != null) {
            timer_div.innerHTML = this.build_remaining_time_str();
        }
        if (this.remaining_time <= 0) {
            clearInterval(this.timer);
        }
    }

    build_remaining_time_str() {
        var time_str = "";
        const min = Math.floor(this.remaining_time / 60);
        const sec = Math.round(this.remaining_time % 60);

        if (min < 10) { time_str += "0"; }
        time_str += min.toString() + ":";
        if (sec < 10) { time_str += "0"; }
        time_str += sec.toString();
        return time_str;
    }

    make_id(length) {
        // Thanks @ https://stackoverflow.com/questions/1349404/generate-random-string-characters-in-javascript/1349426#1349426
       var result           = '';
       var characters       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
       var charactersLength = characters.length;
       for ( var i = 0; i < length; i++ ) {
          result += characters.charAt(Math.floor(Math.random() * charactersLength));
       }
       return result;
    }
}


class SprinklerInterfacePlugin extends BybPluginInterface {

    constructor() {
        super();
        this.name = document.getElementById("sprinkler_interface_plugin_name").innerHTML;

        this.zone_timers = [];  // timer objects to update the UI with remaining time per zone.

        this.watering_state_div_id = "sip_watering_state_label";
        this.duration_input_field_id = "sip_duration_input_field";
        this.zone_picker_id = "sip_select_zone";

        bybConnection.register_plugin(this);
        // this.register();
    }

    receive_data(data) {
        if (data.constructor != Object || !("command" in data) || !("payload" in data)) {
            console.log("sprinkler plugin received invalid data:", data);
            return;
        }

        if (data["command"] == "update_frontend_state") {
            console.log("Will update sprinkler plugin state");
            this.display_updated_watering_state(data["payload"]);
        }
    }

    display_updated_watering_state(actuator_states) {
        this.zone_timers = [];
        var d = "";
        for (var actuator_state of actuator_states) {
            const description = actuator_state["description"];
            const remaining_time = actuator_state["remaining_time"];
            if (remaining_time != null) {
                console.log("received update with remaining time:", Math.round(remaining_time));
                const timer = new ZoneDisplayTimer(Math.round(remaining_time));
                d += description + '<span id="' + timer.time_content_div_id + '">' + timer.build_remaining_time_str() + "</span><br>";
                this.zone_timers.push(timer);
            } else {
                d += description + "<br>";
            }
        }
        const state_field = document.getElementById(this.watering_state_div_id);
        state_field.innerHTML = d;
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