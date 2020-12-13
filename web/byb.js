
class BybPluginInterface {

    // get name() {
    //     return this._name;
    // }

    register() {
        // Registers the plugin at the websocket connection.
        // Once the websocket connection knows this plugin exists, it can
        // forward received messages.
        if (typeof this.name == "undefined") {
            console.log("Failed to register plugin because this.name wasn't set!");
            return;
        }

        bybConnection.register_plugin(this);
    }

    receive_data(data) {
    }

    send_to_backend(data) {
        bybConnection.send_to_backend(data, this);
    }
}


class BybConnection {

    constructor() {
        const ws_addr = "ws://" + location.host + "/ws";
        // console.log(ws_addr);
        this.ws = new WebSocket(ws_addr);
        this.plugins = {};

        this.connection_state_label = document.getElementById("connection_state_label");

        // bind the method like this to make `this` refer to the class instance
        this.ws.onmessage = this.onmessage_callback.bind(this);
        this.ws.onopen = this.onopen_callback.bind(this);
        this.ws.onclose = this.onclose_callback.bind(this);
        this.ws.onerror = this.onerror_callback.bind(this);
    }

    onopen_callback(event) {
        this.connection_state_label.innerHTML = "";
        this.connection_state_label.style.color = "black";
    }

    onclose_callback(event) {
        this.connection_state_label.innerHTML = "Connection to server closed";
        this.connection_state_label.style.color = "darkred";
        console.log("connection to ws server closed:", event);
    }

    onerror_callback(event) {
        this.connection_state_label.innerHTML = "Connection error";
        this.connection_state_label.style.color = "red";
        console.log("connection error:", event);
    }

    onmessage_callback(event) {
        // console.log("BybConnection received data:");
        // console.log(event.data);

        const json_data = JSON.parse(event.data);
        const receiving_plugin = json_data["plugin_name"];

        if (!(receiving_plugin in this.plugins)) {
            console.log("received message for unknown plugin:", receiving_plugin);
            return;
        }

        this.plugins[receiving_plugin].receive_data(json_data["payload"]);
    }

    register_plugin(plugin) {
        if (plugin.name == "") {
            console.log("BybConnection: Didn't add plugin: plugin.name was empty.");
            return;
        }
        this.plugins[plugin.name] = plugin;
        console.log("Registered plugin: ", plugin);
    }

    send_to_backend(json_data, sender) {
        const json_str = JSON.stringify({
            plugin_name: sender.name,
            payload: json_data
        })
        this.ws.send(json_str);
    }

    received_from_backend(json_data) {
    }
}

var bybConnection = new BybConnection();