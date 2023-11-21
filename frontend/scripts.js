const GPTResearcher = (() => {
    const init = () => {
      // Not sure, but I think it would be better to add event handlers here instead of in the HTML
      //document.getElementById("startResearch").addEventListener("click", startResearch);
      document.getElementById("copyToClipboard").addEventListener("click", copyToClipboard);

      updateState("initial");
    }

    const startResearch = () => {
      document.getElementById("output").innerHTML = "";
      document.getElementById("reportContainer").innerHTML = "";
      updateState("in_progress")
  
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
          updateState("finished")
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
  
    const addAgentResponse = (data) => {
      const output = document.getElementById("output");
      output.innerHTML += '<div class="agent_response">' + data.output + '</div>';
      output.scrollTop = output.scrollHeight;
      output.style.display = "block";
      updateScroll();
    };
  
    const writeReport = (data, converter) => {
      const reportContainer = document.getElementById("reportContainer");
      const markdownOutput = converter.makeHtml(data.output);
      reportContainer.innerHTML += markdownOutput;
      updateScroll();
    };
  
    const updateDownloadLink = (data) => {
      const path = data.output;
      document.getElementById("downloadLink").setAttribute("href", path);
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

    const updateState = (state) => {
      var status = "";
      switch (state) {
        case "in_progress":
          status = "Research in progress..."
          setReportActionsStatus("disabled");
          break;
        case "finished":
          status = "Research finished!"
          setReportActionsStatus("enabled");
          break;
        case "error":
          status = "Research failed!"
          setReportActionsStatus("disabled");
          break;
        case "initial":
          status = ""
          setReportActionsStatus("hidden");
          break;
        default:
          setReportActionsStatus("disabled");
      }
      document.getElementById("status").innerHTML = status;
      if (document.getElementById("status").innerHTML == "") {
        document.getElementById("status").style.display = "none";
      } else {
        document.getElementById("status").style.display = "block";
      }
    }

    /**
     * Shows or hides the download and copy buttons
     * @param {str} status Kind of hacky. Takes "enabled", "disabled", or "hidden". "Hidden is same as disabled but also hides the div"
     */
    const setReportActionsStatus = (status) => {
      const reportActions = document.getElementById("reportActions");
      // Disable everything in reportActions until research is finished

      if (status == "enabled") {
        reportActions.querySelectorAll("a").forEach((link) => {
          link.classList.remove("disabled");
          link.removeAttribute('onclick');
          reportActions.style.display = "block";
        });
      } else {
        reportActions.querySelectorAll("a").forEach((link) => {
          link.classList.add("disabled");
          link.setAttribute('onclick', "return false;");
        });
        if (status == "hidden") {
          reportActions.style.display = "none";
        }
      }
    }

    const fetchAndDisplayConfig = () => {
      fetch('/get-config')
      .then(response => {
          if (!response.ok) {
              throw new Error('Network response was not ok');
          }
          return response.json();
      })
      .then(data => {
          const { config, descriptions } = data;
          const configFields = document.getElementById('configFields');
          configFields.innerHTML = '';
  
          Object.keys(config).forEach(key => {
              configFields.innerHTML += `
                  <div class="form-group">
                      <label>${key}</label>
                      <small class="small-description">${descriptions[key]}</small>
                      <input type="text" class="form-control" id="config-${key}" value="${config[key]}">
                      
                  </div>
              `;
          });
  
          configFields.innerHTML += `
              <button onclick="GPTResearcher.updateAllConfigs()" class="btn btn-primary update-all-configs">Update All Configurations</button>`;
          initializeCollapsible();
      })
      .catch((error) => {
          console.error('Error:', error);
      });
    };
  
    // Function to initialize collapsible element
    const initializeCollapsible = () => {
      const collapsible = document.querySelector(".collapsible");
      if (collapsible) {
          const content = collapsible.nextElementSibling;
          collapsible.addEventListener("click", function() {
              this.classList.toggle("active");
              if (content.style.display === "block" || content.style.display === "") {
                  content.style.display = "none";
              } else {
                  content.style.display = "block";
              }
          });

          // Start with the configuration section collapsed
          content.style.display = "none";
        }
    };

    
    const updateAllConfigs = () => {
      const configFields = document.getElementById('configFields');
      const inputs = configFields.getElementsByTagName('input');
      const updates = Array.from(inputs).map(input => {
          return { key: input.id.replace('config-', ''), value: input.value };
      });
  
      fetch('/update-configs', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify(updates)
      })
      .then(response => response.json())
      .then(data => {
          if (data.every(update => update.status === "success")) {
              alert('All configurations have been updated successfully.');
          } else {
              const failedUpdates = data.filter(update => update.status !== "success");
              alert('Failed to update configurations: ' + failedUpdates.map(update => update.key).join(', '));
          }
      })
      .catch((error) => {
          console.error('Error:', error);
          alert('Failed to update configurations.');
      });
    };

  document.addEventListener("DOMContentLoaded", () => {
      init();
      fetchAndDisplayConfig();
  });

    return {
      startResearch,
      copyToClipboard,
      updateAllConfigs,
    };
  })();