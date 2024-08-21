const GPTResearcher = (() => {
  const init = () => {
    // Not sure, but I think it would be better to add event handlers here instead of in the HTML
    //document.getElementById("startResearch").addEventListener("click", startResearch);
    document
      .getElementById('copyToClipboard')
      .addEventListener('click', copyToClipboard)

    updateState('initial')
  }

  const changeSource = () => {
    const report_source = document.querySelector('select[name="report_source"]').value
    if (report_source === 'sources') {
        document.getElementById('sources').style.display = 'block'
    } else {
        document.getElementById('sources').style.display = 'none'
    }
  }

  const startResearch = () => {
    document.getElementById('output').innerHTML = ''
    document.getElementById('reportContainer').innerHTML = ''
    updateState('in_progress')

    addAgentResponse({
      output: '🤔 Thinking about research questions for the task...',
    })

    listenToSockEvents()
  }

  const listenToSockEvents = () => {
    const { protocol, host, pathname } = window.location
    const ws_uri = `${
      protocol === 'https:' ? 'wss:' : 'ws:'
    }//${host}${pathname}ws`
    const converter = new showdown.Converter()
    const socket = new WebSocket(ws_uri)

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'logs') {
        addAgentResponse(data)
      } else if (data.type === 'report') {
        writeReport(data, converter)
      } else if (data.type === 'path') {
        updateState('finished')
        updateDownloadLink(data)
      }
    }

    socket.onopen = (event) => {
      const task = document.querySelector('input[name="task"]').value
      const report_type = document.querySelector(
        'select[name="report_type"]'
      ).value
      const report_source = document.querySelector(
        'select[name="report_source"]'
      ).value
      const tone = document.querySelector('select[name="tone"]').value
      const agent = document.querySelector('input[name="agent"]:checked').value
      let source_urls = tags

      if (report_source !== 'sources' && source_urls.length > 0) {
        source_urls = source_urls.slice(0, source_urls.length - 1)
      }

      const requestData = {
        task: task,
        report_type: report_type,
        report_source: report_source,
        source_urls: source_urls,
        tone: tone,
        agent: agent,
      }

      socket.send(`start ${JSON.stringify(requestData)}`)
    }
  }

  const addAgentResponse = (data) => {
    const output = document.getElementById('output')
    output.innerHTML += '<div class="agent_response">' + data.output + '</div>'
    output.scrollTop = output.scrollHeight
    output.style.display = 'block'
    updateScroll()
  }

  const writeReport = (data, converter) => {
    const reportContainer = document.getElementById('reportContainer')
    const markdownOutput = converter.makeHtml(data.output)
    reportContainer.innerHTML += markdownOutput
    updateScroll()
  }

  const updateDownloadLink = (data) => {
    const pdf_path = data.output.pdf
    const docx_path = data.output.docx
    const md_path = data.output.md;
    document.getElementById('downloadLink').setAttribute('href', pdf_path);
    document.getElementById('downloadLinkWord').setAttribute('href', docx_path);
    document.getElementById("downloadLinkMd").setAttribute("href", md_path);
  }

  const updateScroll = () => {
    window.scrollTo(0, document.body.scrollHeight)
  }

  const copyToClipboard = () => {
    const textarea = document.createElement('textarea')
    textarea.id = 'temp_element'
    textarea.style.height = 0
    document.body.appendChild(textarea)
    textarea.value = document.getElementById('reportContainer').innerText
    const selector = document.querySelector('#temp_element')
    selector.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }

  const updateState = (state) => {
    var status = ''
    switch (state) {
      case 'in_progress':
        status = 'Research in progress...'
        setReportActionsStatus('disabled')
        break
      case 'finished':
        status = 'Research finished!'
        setReportActionsStatus('enabled')
        break
      case 'error':
        status = 'Research failed!'
        setReportActionsStatus('disabled')
        break
      case 'initial':
        status = ''
        setReportActionsStatus('hidden')
        break
      default:
        setReportActionsStatus('disabled')
    }
    document.getElementById('status').innerHTML = status
    if (document.getElementById('status').innerHTML == '') {
      document.getElementById('status').style.display = 'none'
    } else {
      document.getElementById('status').style.display = 'block'
    }
  }

  /**
   * Shows or hides the download and copy buttons
   * @param {str} status Kind of hacky. Takes "enabled", "disabled", or "hidden". "Hidden is same as disabled but also hides the div"
   */
  const setReportActionsStatus = (status) => {
    const reportActions = document.getElementById('reportActions')
    // Disable everything in reportActions until research is finished

    if (status == 'enabled') {
      reportActions.querySelectorAll('a').forEach((link) => {
        link.classList.remove('disabled')
        link.removeAttribute('onclick')
        reportActions.style.display = 'block'
      })
    } else {
      reportActions.querySelectorAll('a').forEach((link) => {
        link.classList.add('disabled')
        link.setAttribute('onclick', 'return false;')
      })
      if (status == 'hidden') {
        reportActions.style.display = 'none'
      }
    }
  }

  const tagsInput = document.getElementById('tags-input');
  const input = document.getElementById('custom_source');

  const tags = [];

  const addTag = (url) => {
    if (tags.includes(url)) return;
    tags.push(url);

    const tagElement = document.createElement('span');
    tagElement.className = 'tag';
    tagElement.textContent = url;

    const removeButton = document.createElement('span');
    removeButton.className = 'remove-tag';
    removeButton.textContent = 'x';
    removeButton.onclick = function () {
        tagsInput.removeChild(tagElement);
        tags.splice(tags.indexOf(url), 1);
    };

    tagElement.appendChild(removeButton);
    tagsInput.insertBefore(tagElement, input);
  }

  document.addEventListener('DOMContentLoaded', init)
  return {
    startResearch,
    copyToClipboard,
    changeSource,
      addTag,
  }
})()
