const startResearch = () => {
    // Clear output and reportContainer divs

    document.getElementById("output").innerHTML = "";
    document.getElementById("reportContainer").innerHTML = "";

    addAgentResponse({output: "🤔 Thinking about research questions for the task..."});

    listenToSockEvents();
}

const listenToSockEvents = () => {
    const converter = new showdown.Converter();
    const socket = new WebSocket("ws://localhost:8000/ws");
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'logs') {
            addAgentResponse(data);
        } else if (data.type === 'report') {
            writeReport(data, converter);
        } else if (data.type === 'path') {
            updateDownloadLink(data);
        }
    };
    socket.onopen = (event) => {
        let task = document.querySelector('input[name="task"]').value;
        let report_type = document.querySelector('select[name="report_type"]').value;
        let agent = document.querySelector('input[name="agent"]:checked').value;
        let api_key = document.querySelector('input[name="api_key"]').value; // Get the API key from the input field
        let data = "start " + JSON.stringify({task: task, report_type: report_type, agent: agent, api_key: api_key}); // Include the API key in the data
        socket.send(data);
    };
}

const addAgentResponse = (data) => {
    const output = document.getElementById("output");
    output.innerHTML += '<div class="agent_response">'+data.output+'</div>';
    output.scrollTop = output.scrollHeight;  // Scroll to the bottom of the output
    output.style.display = "block";
    updateScroll();
}

const writeReport = (data, converter) => {
    const reportContainer = document.getElementById("reportContainer");
    const markdownOutput = converter.makeHtml(data.output);
    reportContainer.innerHTML += markdownOutput;
    updateScroll();
}

const updateDownloadLink = (data) => {
    const path = data.output;
    const downloadLink = document.getElementById("downloadLink");
    downloadLink.href = path;
}

const updateScroll = () => {
    window.scrollTo(0,document.body.scrollHeight);
}

const copyToClipboard = () => {
    const textarea = document.createElement('textarea');
    textarea.id = 'temp_element';
    textarea.style.height = 0;
    document.body.appendChild(textarea);
    textarea.value = document.getElementById('reportContainer').innerText;
    const selector = document.querySelector('#temp_element');
    selector.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
}
