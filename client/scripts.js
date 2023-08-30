const GPTResearcher = (() => {
    const startResearch = () => {
      document.getElementById("output").innerHTML = "";
      document.getElementById("reportContainer").innerHTML = "";
  
      addAgentResponse({ output: "🤔 Thinking about research questions for the task..." });
  
      listenToSockEvents();
    };
  
    const listenToSockEvents = () => {
      const { protocol, host, pathname } = window.location;
      const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${host}${pathname}ws`;
      const converter = new showdown.Converter();
      const socket = new WebSocket(ws_uri);
  
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
        const task = document.querySelector('input[name="task"]').value;
        const report_type = document.querySelector('select[name="report_type"]').value;
        const agent = document.querySelector('input[name="agent"]:checked').value;
  
        const requestData = {
          task: task,
          report_type: report_type,
          agent: agent,
        };
  
        socket.send(`start ${JSON.stringify(requestData)}`);
      };
    };

    let agentMarkdownContent = "";
  
    const addAgentResponse = (data) => {
      const output = document.getElementById("output");
      output.innerHTML += '<div class="agent_response">' + data.output + '</div>';
      agentMarkdownContent += data.output;
      output.scrollTop = output.scrollHeight;
      output.style.display = "block";
      updateScroll();
    };
  
    let markdownContent = "";

    const writeReport = (data, converter) => {
      const reportContainer = document.getElementById("reportContainer");
      const markdownOutput = converter.makeHtml(data.output);
      markdownContent += data.output;
      reportContainer.innerHTML += markdownOutput;
      document.getElementById('downloadObsidian').disabled = false;
      document.getElementById('copyToClipboard').disabled = false;
      updateScroll();
    };
  
    const updateDownloadLink = (data) => {
      const path = data.output;
      const downloadLink = document.getElementById("downloadLink");
      downloadLink.href = path;
    };
  
    const updateScroll = () => {
      window.scrollTo(0, document.body.scrollHeight);
    };
  
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
    };

    const sendToObsidian = async () => {
      let template;
      try {
        const response = await fetch('/site/obsidian_template.md');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        template = await response.text();
      } catch (e) {
        console.log('There was an error fetching the template: ', e);
      }

      if (template) {
        const prompt = document.querySelector('#task').value;
        template = template.replace('{PROMPT}', prompt);
        template = template.replace('{RESEARCH_REPORT}', markdownContent);
        template = template.replace('{AGENT_OUTPUT}', agentMarkdownContent);
      } else {
        console.log('Template is not defined. Check fetch operation.');
      }

      fetch('/obsidian', {
        method: 'POST',
        headers: {
          'Content-Type': 'text/plain'
        },
        body: template
      })
    };
  
    return {
      startResearch,
      copyToClipboard,
      sendToObsidian,
    };
  })();
