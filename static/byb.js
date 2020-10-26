
class BybPluginInterface {

    get name() {
        return ""
    }

    receive_data(data) {
    }
}


class BybConnection {

    constructor() {
        const ws_addr = "ws://" + location.host + "/websocket";
        console.log(ws_addr);
        this.ws = new WebSocket(ws_addr);
        this.plugins = {};

        this.ws.onmessage = function(event) {
            console.log("BybConnection received data:");
            console.log(event.data);
        }
    }

    register_plugin(plugin) {
        if (plugin.name == "") {
            console.log("BybConnection: Didn't add plugin: plugin.name was empty.");
            return;
        }
        this.plugins[plugin.name] = plugin;
    }

    send_to_backend(json_data) {
        this.ws.send(JSON.stringify(json_data));
    }

    received_from_backend(json_data) {

    }
}

var bc = new BybConnection();