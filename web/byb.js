
class BybPluginInterface {

    // get name() {
    //     return this._name;
    // }

    receive_data(data) {
    }
}


class BybConnection {

    constructor() {
        const ws_addr = "ws://" + location.host + "/ws";
        console.log(ws_addr);
        this.ws = new WebSocket(ws_addr);
        this.plugins = {};

        // bind the method like this to make `this` refer to the class instance
        this.ws.onmessage = this.onmessage_callback.bind(this);
    }

    onmessage_callback(event) {
        console.log("BybConnection received data:");
        console.log(event.data);

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

    send_to_backend(json_data) {
        this.ws.send(JSON.stringify(json_data));
    }

    received_from_backend(json_data) {
    }
}

var bybConnection = new BybConnection();