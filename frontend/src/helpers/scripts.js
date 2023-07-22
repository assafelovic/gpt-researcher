export const addAgentResponse = (data) => {
    const output = document.getElementById("output");
    // output.innerHTML += '<div class="agent_response">'+data.output+'</div>';
    // output.scrollTop = output.scrollHeight;  // Scroll to the bottom of the output
    // output.style.display = "block";
    updateScroll();
}

export const writeReport = (data, converter) => {
    const reportContainer = document.getElementById("reportContainer");
    const markdownOutput = converter.makeHtml(data.output);
    reportContainer.innerHTML += markdownOutput;
    updateScroll();
}

export const updateDownloadLink = (data) => {
    const path = data.output;
    const downloadLink = document.getElementById("downloadLink");
    downloadLink.href = path;
}

export const updateScroll = () => {
    window.scrollTo(0,document.body.scrollHeight);
}
