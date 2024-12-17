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

    const imageContainer = document.getElementById('selectedImagesContainer')
    imageContainer.innerHTML = ''
    imageContainer.style.display = 'none'

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
      console.log("Received message:", data);  // Debug log
      if (data.type === 'logs') {
        addAgentResponse(data)
      } else if (data.type === 'images') {
      console.log("Received images:", data);  // Debug log
        displaySelectedImages(data)
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
    if (!data.output) {
        console.error('No output data received');
        return;
    }
    
    const { pdf, docx, md, json } = data.output;
    console.log('Received paths:', { pdf, docx, md, json });
    
    // Helper function to safely update link
    const updateLink = (id, path) => {
        const element = document.getElementById(id);
        if (element && path) {
            console.log(`Setting ${id} href to:`, path);
            element.setAttribute('href', path);
            element.classList.remove('disabled');
        } else {
            console.warn(`Either element ${id} not found or path not provided`);
        }
    };

    updateLink('downloadLink', pdf);
    updateLink('downloadLinkWord', docx);
    updateLink('downloadLinkMd', md);
    updateLink('downloadLinkJson', json);
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

  const displaySelectedImages = (data) => {
    const imageContainer = document.getElementById('selectedImagesContainer')
    //imageContainer.innerHTML = '<h3>Selected Images</h3>'
    const images = JSON.parse(data.output)
    console.log("Received images:", images);  // Debug log
    if (images && images.length > 0) {
      images.forEach(imageUrl => {
        const imgElement = document.createElement('img')
        imgElement.src = imageUrl
        imgElement.alt = 'Research Image'
        imgElement.style.maxWidth = '200px'
        imgElement.style.margin = '5px'
        imgElement.style.cursor = 'pointer'
        imgElement.onclick = () => showImageDialog(imageUrl)
        imageContainer.appendChild(imgElement)
      })
      imageContainer.style.display = 'block'
    } else {
      imageContainer.innerHTML += '<p>No images found for this research.</p>'
    }
  }

  const showImageDialog = (imageUrl) => {
    const dialog = document.createElement('div');
    dialog.className = 'image-dialog';
    
    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = 'Full-size Research Image';
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.onclick = () => document.body.removeChild(dialog);
    
    dialog.appendChild(img);
    dialog.appendChild(closeBtn);
    document.body.appendChild(dialog);
  }

  document.addEventListener('DOMContentLoaded', init)
  return {
    startResearch,
    copyToClipboard,
    changeSource,
    addTag,
    displaySelectedImages,
    showImageDialog,
  }
})()
