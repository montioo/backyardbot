
function on() {
    document.getElementById("overlay").style.display = "block";
}

function off() {
    document.getElementById("overlay").style.display = "none";
}

function clicked_selector(sender) {
    // toggle selector
    const selected_class = "selector_box_selected";
    toggle_class_list(sender, selected_class);
}

function toggle_class_list(element, class_name) {
    // toggles the presence of the given class string and returns whether the class is present afterwards.
    if (element.classList.contains(class_name)) {
        element.classList.remove(class_name);
        return false;
    }
    element.classList.add(class_name);
    return true;
}

function time_changed(sender) {
    console.log(sender.value);
    const valid_class = "time_picker_filled";
    if (sender.value.length == 0) {
        sender.classList.remove(valid_class);
        return;
    }
    sender.classList.add(valid_class);
}

console.log("test");