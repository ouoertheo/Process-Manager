/**
 * @type {import('jquery')}
 */
const $ = jQuery;

/**
 * @type {import('toastr')}
 */

/**
 *  @type {import('CodeMirror')}
 */

function setProcessControlButton(button, processStatus){
    if (processStatus == "running"){
        button.removeClass("btn-success")
        button.addClass("btn-danger")
        button.text("Stop")
    } else if (processStatus == "stopped"){
        button.removeClass("btn-danger")
        button.addClass("btn-success")
        button.text("Start")
    }
}


// Poll for process logs
function pollProcesses() {
    $.getJSON('/processes', function(data) {
        data.forEach(process => {
            if (process.logs.length > 0) {
                $(`#log-${process.name}`).text(process.logs.join('\n'));
            }
            // Set the correct button type
            setProcessControlButton($(`#btn-${process.name}`), process.status)
        });
        setTimeout(pollProcesses, 5000);
    });
}

pollProcesses();

// Refresh processes and reload the page
function loadProcessConfig() {
    $.post('/processes/reload', function(data) {
        editor.setValue(JSON.stringify(data, null, 2))
        editor.refresh()
    }).then(() => {
    });
}

// Save processes and update editor
function saveProcessConfig() {
    const updatedProcessDefs = editor.getValue();

    $.post({
        url: '/processes/update',
        data: updatedProcessDefs,
        contentType: 'application/json',
    }).done(() => {
        loadProcessConfig();
        toastr.success("Updated process configs.")
    }).fail(error => {
        let errorText
        if (error.statusText.includes('Unprocessable')){
            errorText = `Failed to update process configs: Invalid JSON`
        } else {
            errorText = error.responseText
        }
        toastr.error(errorText)
    });
}

const readProcessConfigButton = document.getElementById('btn-read-process-config');
const saveProcessConfigButton = document.getElementById('btn-save-process-config');
readProcessConfigButton.addEventListener('click', loadProcessConfig);
saveProcessConfigButton.addEventListener('click', saveProcessConfig);

// Handle starting and stopping of process
const processControlButtons = document.getElementsByClassName('btn-process-control')
async function startStopProcess(event) {
    const target = event.target
    const processName = target.getAttribute('data-process-name')
    const controlButton = $(`#btn-${processName}`)

    // Get the current process and set button accordingly
    let process
    await $.getJSON(`/processes/${processName}`, function(data) {
        process = data
    })
    
    // Set whether to perform start or stop
    let command
    if (process.status == "running"){
        command = "stop"
        setProcessControlButton(controlButton, "stopped")
    } else if (process.status == "stopped") {
        command = "start"
        setProcessControlButton(controlButton, "running")
    }

    console.log(`Starting ${processName}`)
    $.post({
        url:`/processes/${processName}/${command}`,
        data: {name: processName},
        contentType: 'application/json'
    }).done(process => {
        if (process.status == "running"){
            toastr.success(`Started ${processName}.`)
        } else if (process.status == "stopped") {
            toastr.success(`Stopped ${processName}`)
        }
    }).fail(error => {
        toastr.error(`Failed to start process: ${error.responseText}`)
    })
}

for (element of processControlButtons) {
    element.addEventListener('click',startStopProcess)
}

// Initialize CodeMirror editor
const processDefsTextarea = document.getElementById('process-defs');
const editor = CodeMirror.fromTextArea(processDefsTextarea, {
    lineNumbers: true,
    mode: 'application/json',
    theme: 'material-darker',
    autoRefresh: true,
    foldGutter: true,
    gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
});

// Adjust CodeMirror editor height based on content
function adjustEditorHeight() {
    const contentHeight = editor.getScrollInfo().height;
    const maxEditorHeight = parseInt(getComputedStyle(editor.getWrapperElement()).maxHeight, 10);

    editor.setSize(null, contentHeight < maxEditorHeight ? contentHeight : maxEditorHeight);
}
// Adjust editor height initially and when content changes
adjustEditorHeight();
editor.on('change', adjustEditorHeight);
