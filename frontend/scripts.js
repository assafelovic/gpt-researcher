const GPTResearcher = (() => {
  // Track if initial scroll has been performed
  let hasScrolledToOutput = false;

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
      output: '🧙‍♂️ Gathering information and analyzing your research topic...',
    })

    // Reset the scroll flag when starting new research
    hasScrolledToOutput = false

    // Initial scroll to output area
    scrollToOutput()

    listenToSockEvents()
  }

  const listenToSockEvents = () => {
    const { protocol, host, pathname } = window.location
    const ws_uri = `${
      protocol === 'https:' ? 'wss:' : 'ws:'
    }//${host}${pathname}ws`

    // Configure Showdown converter to properly handle code blocks
    const converter = new showdown.Converter({
      ghCodeBlocks: true,         // GitHub style code blocks
      tables: true,               // Enable tables
      tasklists: true,            // Enable task lists
      smartIndentationFix: true,  // Fix weird indentation
      simpleLineBreaks: true,     // Treat newlines as <br>
      openLinksInNewWindow: true, // Open links in new tab
      parseImgDimensions: true    // Parse image dimensions from markdown
    });

    // Fix issues with code block formatting
    converter.setOption('literalMidWordUnderscores', true);

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
    output.scrollTop = output.scrollHeight // Auto-scroll within output container
    output.style.display = 'block'
  }

  const writeReport = (data, converter) => {
    const reportContainer = document.getElementById('reportContainer')

    // Ensure code blocks maintain formatting
    let processedOutput = data.output;

    // Process code blocks to preserve formatting
    processedOutput = processedOutput.replace(/```(\w*)\n([\s\S]*?)\n```/g, function(match, lang, code) {
      // Preserve newlines and indentation in code blocks
      return '```' + lang + '\n' + code + '\n```';
    });

    const markdownOutput = converter.makeHtml(processedOutput)
    reportContainer.innerHTML += markdownOutput
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
    // Function intentionally left empty to prevent auto-scrolling
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

    // Show a temporary success message
    const copyBtn = document.getElementById('copyToClipboard');
    const originalText = copyBtn.textContent;
    copyBtn.textContent = 'Copied!';
    setTimeout(() => {
      copyBtn.textContent = originalText;
    }, 2000);
  }

  const updateState = (state) => {
    var status = ''
    switch (state) {
      case 'in_progress':
        status = 'Research in progress... Please wait'
        setReportActionsStatus('disabled')
        break
      case 'finished':
        status = 'Research complete! Your report is ready'
        setReportActionsStatus('enabled')
        break
      case 'error':
        status = 'Research failed. Please try again'
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
      imageContainer.innerHTML = '<h3>Research Images</h3>'
      images.forEach(imageUrl => {
        const imgElement = document.createElement('img')
        imgElement.src = imageUrl
        imgElement.alt = 'Research Image'
        imgElement.onclick = () => showImageDialog(imageUrl)
        imageContainer.appendChild(imgElement)
      })
      imageContainer.style.display = 'block'
    } else {
      imageContainer.innerHTML += '<p>No images found for this research.</p>'
    }
  }

  const showImageDialog = (imageUrl) => {
    const dialog = document.createElement('div')
    dialog.className = 'image-dialog'

    const img = document.createElement('img')
    img.src = imageUrl
    img.alt = 'Full Size Image'

    const closeButton = document.createElement('button')
    closeButton.textContent = 'Close'
    closeButton.onclick = () => document.body.removeChild(dialog)

    dialog.appendChild(img)
    dialog.appendChild(closeButton)
    document.body.appendChild(dialog)
  }

  // Renamed function to be more descriptive and only scroll once
  const scrollToOutput = () => {
    if (!hasScrolledToOutput) {
      const outputElement = document.getElementById('output')
      if (outputElement) {
        outputElement.scrollIntoView({ behavior: 'smooth' })
        hasScrolledToOutput = true
      }
    }
  }

  return {
    init,
    changeSource,
    startResearch,
    addTag,
    copyToClipboard
  }
})()

window.addEventListener('DOMContentLoaded', GPTResearcher.init)
