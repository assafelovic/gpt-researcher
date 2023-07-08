function copyToClipboard() {
    var textarea = document.createElement('textarea');
    textarea.id = 'temp_element';
    textarea.style.height = 0;
    document.body.appendChild(textarea);
    textarea.value = document.getElementById('reportContainer').innerText;
    var selector = document.querySelector('#temp_element');
    selector.select();
    document.execCommand('copy');
    // Remove the <textarea> element
    document.body.removeChild(textarea);
}

function startResearch() {
    // Clear output and reportContainer divs
    document.getElementById("output").innerHTML = "";
    document.getElementById("reportContainer").innerHTML = "";

    const converter = new showdown.Converter();
    const socket = new WebSocket("ws://localhost:8000/ws");
    socket.onmessage = function(event) {
        console.log(event.data);
        const data = JSON.parse(event.data);
        if (data.type === 'logs') {
            // Append the agent output to the output section
            const output = document.getElementById("output");
            output.innerHTML += "<br>"+data.output+"<br>";
            output.scrollTop = output.scrollHeight;  // Scroll to the bottom of the output
            output.style.display = "block";
        } else if (data.type === 'report') {
            // Update the report section with new data
            const reportContainer = document.getElementById("reportContainer");
            const markdownOutput = converter.makeHtml(data.output);
            reportContainer.innerHTML += markdownOutput;
            updateScroll();
        } else if (data.type === 'path') {
            // Update the download link with the received path
            const path = data.output;
            const downloadLink = document.getElementById("downloadLink");
            downloadLink.href = path;
        }
    };
    socket.onopen = function (event) {
        let task = document.querySelector('textarea[name="task"]').value;
        let report_type = document.querySelector('select[name="report_type"]').value;
        let data = "start " + JSON.stringify({task: task, report_type: report_type});
        socket.send(data);
    };
    function updateScroll() {
        window.scrollTo(0,document.body.scrollHeight);
    }
}