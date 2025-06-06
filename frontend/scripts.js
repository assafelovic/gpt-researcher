const GPTResearcher = (() => {
  let isResearchActive = false;
  let connectionTimeout = null;
  let conversationHistory = [];
  let isInitialLoad = true; // Flag to track initial page load
  let cookiesEnabled = true; // Flag to track if cookies are enabled
  let allReports = ''; // Store all reports cumulatively
  let currentReport = ''; // Store the current report (will be overwritten)
  let isFirstReport = true; // Flag to track if this is the first report
  let chatContainer = null; // Global reference to chat container
  let lastRequestData = null; // Store the last request data for reconnection

  // Add WebSocket monitoring variables
  let socket = null;
  let connectionStartTime = null;
  let lastActivityTime = null;
  let connectionAttempts = 0;
  let messagesReceived = 0;
  let websocketMonitorInterval = null;
  let dispose_socket = null; // Re-add dispose_socket
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 5;
  let reconnectInterval = 2000; // Start with 2 seconds

  const init = () => {
    // Check if cookies are enabled
    checkCookiesEnabled();

    // Load history immediately on page load
    loadConversationHistory();

    // After a short delay, mark initial load as complete
    setTimeout(() => {
      isInitialLoad = false;
    }, 1000);

    // Setup form submission
    document.getElementById('researchForm').addEventListener('submit', (e) => {
      e.preventDefault();
      startResearch();
      return false;
    });

    document
      .getElementById('copyToClipboard')
      .addEventListener('click', copyToClipboard)

    // Add event listener for the top copy button
    const topCopyButton = document.getElementById('copyToClipboardTop');
    if (topCopyButton) {
      topCopyButton.addEventListener('click', copyToClipboard);
    }

    // Initialize expand buttons
    initExpandButtons();

    // Initialize history panel functionality
    initHistoryPanel();

    // Initialize WebSocket monitoring panel
    initWebSocketPanel();

    // Initialize MCP functionality
    initMCPSection();

    // The download bar is now fixed in place with CSS
    // No need to set display property here

    updateState('initial');

    // Initialize research icon to not spinning
    updateResearchIcon(false);

    // Hide loading overlay if it exists
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
      loadingOverlay.classList.add('loading-hidden');
    }
  }

  // Check if cookies are enabled
  const checkCookiesEnabled = () => {
    try {
      // Try to set a test cookie
      document.cookie = "testcookie=1; path=/";
      const cookieEnabled = document.cookie.indexOf("testcookie") !== -1;

      if (!cookieEnabled) {
        console.warn("Cookies are disabled in this browser");
        cookiesEnabled = false;
        showToast("Cookies are disabled. History will use localStorage instead.", 5000);
      } else {
        // Clean up test cookie
        document.cookie = "testcookie=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        cookiesEnabled = true;
      }

      return cookieEnabled;
    } catch (e) {
      console.error("Error checking cookies:", e);
      cookiesEnabled = false;
      return false;
    }
  }

  // Initialize conversation history panel functionality
  const initHistoryPanel = () => {
    // Load history from cookie
    loadConversationHistory();

    // Setup history panel toggle button
    const historyPanelOpenBtn = document.getElementById('historyPanelOpenBtn');
    const historyPanel = document.getElementById('historyPanel');
    const historyPanelToggle = document.getElementById('historyPanelToggle');

    if (historyPanelOpenBtn) {
      historyPanelOpenBtn.addEventListener('click', () => {
        loadConversationHistory(); // Reload history when opening panel
        historyPanel.classList.add('open');
      });
    }

    if (historyPanelToggle) {
      historyPanelToggle.addEventListener('click', () => {
        historyPanel.classList.remove('open');
      });
    }

    // Close panel when clicking outside
    document.addEventListener('click', (e) => {
      // If the panel is open and the click is outside the panel and not on the toggle button
      if (historyPanel.classList.contains('open') &&
        !historyPanel.contains(e.target) &&
        e.target !== historyPanelOpenBtn &&
        !historyPanelOpenBtn.contains(e.target)) {
        historyPanel.classList.remove('open');
      }
    });

    // Setup search functionality
    const historySearch = document.getElementById('historySearch');
    const historySearchBtn = document.getElementById('historySearchBtn');

    if (historySearch && historySearchBtn) {
      historySearch.addEventListener('input', filterHistoryEntries);
      historySearchBtn.addEventListener('click', () => filterHistoryEntries());
    }

    // Setup sort functionality
    const historySortOrder = document.getElementById('historySortOrder');
    if (historySortOrder) {
      historySortOrder.addEventListener('change', () => {
        sortHistoryEntries(historySortOrder.value);
        renderHistoryEntries();
      });
    }

    // Setup clear history button
    const historyClearBtn = document.getElementById('historyClearBtn');
    if (historyClearBtn) {
      historyClearBtn.addEventListener('click', clearConversationHistory);
    }

    // Add action buttons to history panel
    const historyFilters = document.querySelector('.history-panel-filters');
    if (historyFilters) {
      // Create a container for the buttons
      const actionsContainer = document.createElement('div');
      actionsContainer.className = 'history-actions-container';

      // Add export history button with enhanced styling and tooltip
      const exportBtn = document.createElement('button');
      exportBtn.className = 'history-action-btn';
      exportBtn.title = 'Export research history to file';
      exportBtn.innerHTML = '<i class="fas fa-file-export"></i>';
      exportBtn.addEventListener('click', exportHistory);

      // Add import history button with enhanced styling and tooltip
      const importBtn = document.createElement('button');
      importBtn.className = 'history-action-btn';
      importBtn.title = 'Import research history from file';
      importBtn.innerHTML = '<i class="fas fa-file-import"></i>';
      importBtn.addEventListener('click', triggerImportHistory);

      // Add cookie debug button with enhanced styling and tooltip
      const debugBtn = document.createElement('button');
      debugBtn.className = 'history-action-btn';
      debugBtn.title = 'Check storage status';
      debugBtn.innerHTML = '<i class="fas fa-database"></i>';
      debugBtn.addEventListener('click', checkCookieStatus);

      // Add buttons to container in a logical order
      actionsContainer.appendChild(importBtn);
      actionsContainer.appendChild(exportBtn);
      actionsContainer.appendChild(debugBtn);

      // Create a hidden file input for importing
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.id = 'historyFileInput';
      fileInput.accept = '.json';
      fileInput.style.display = 'none';
      fileInput.addEventListener('change', handleFileImport);

      // Add container and file input to filters
      historyFilters.appendChild(actionsContainer);
      historyFilters.appendChild(fileInput);
    }

    // Initial render of history entries
    renderHistoryEntries();
  }

  // Initialize WebSocket monitoring panel
  const initWebSocketPanel = () => {
    const websocketPanel = document.getElementById('websocketPanel');
    const websocketPanelOpenBtn = document.getElementById('websocketPanelOpenBtn');
    const websocketPanelToggle = document.getElementById('websocketPanelToggle');

    if (!websocketPanel || !websocketPanelOpenBtn || !websocketPanelToggle) {
      console.error("WebSocket panel elements not found");
      return;
    }

    console.log("Initializing WebSocket panel");

    // Ensure it starts hidden
    websocketPanel.classList.remove('open');

    websocketPanelOpenBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log("Opening WebSocket panel");
      websocketPanel.classList.add('open');
    });

    websocketPanelToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log("Closing WebSocket panel");
      websocketPanel.classList.remove('open');
    });

    // Close panel when clicking outside
    document.addEventListener('click', (e) => {
      // If the panel is open and the click is outside the panel and not on the toggle button
      if (websocketPanel.classList.contains('open') &&
        !websocketPanel.contains(e.target) &&
        e.target !== websocketPanelOpenBtn &&
        !websocketPanelOpenBtn.contains(e.target)) {
        websocketPanel.classList.remove('open');
      }
    });

    // Start periodic WebSocket status updates
    startWebSocketMonitoring();
  }

  // Start WebSocket monitoring
  const startWebSocketMonitoring = () => {
    console.log("Starting WebSocket monitoring");

    // Update status immediately
    updateWebSocketStatus();

    // Clear any existing interval
    if (websocketMonitorInterval) {
      clearInterval(websocketMonitorInterval);
    }

    // Update status every 2 seconds
    websocketMonitorInterval = setInterval(updateWebSocketStatus, 2000);
  }

  // Update WebSocket status in the panel
  const updateWebSocketStatus = () => {
    // Only proceed if the necessary elements exist
    const connectionStatusEl = document.getElementById('connectionStatus');
    const connectionIndicatorEl = document.getElementById('connectionIndicator');
    const researchStatusEl = document.getElementById('researchStatus');
    const connectionDurationEl = document.getElementById('connectionDuration');
    const lastActivityEl = document.getElementById('lastActivity');
    const readyStateEl = document.getElementById('readyState');
    const connectionAttemptsEl = document.getElementById('connectionAttempts');
    const messagesReceivedEl = document.getElementById('messagesReceived');
    const currentTaskEl = document.getElementById('currentTask');

    if (!connectionStatusEl || !connectionIndicatorEl) return;

    // Update connection status
    const socketStatus = getSocketStatus();
    connectionStatusEl.textContent = socketStatus.statusText;

    // Update indicator class
    connectionIndicatorEl.className = 'status-indicator';
    connectionIndicatorEl.classList.add(socketStatus.indicatorClass);

    // Update research status
    if (researchStatusEl) {
      researchStatusEl.textContent = isResearchActive ? 'Active' : 'Inactive';
    }

    // Update connection duration
    if (connectionDurationEl && connectionStartTime) {
      const duration = Math.floor((Date.now() - connectionStartTime) / 1000);
      connectionDurationEl.textContent = formatDuration(duration);
    } else if (connectionDurationEl) {
      connectionDurationEl.textContent = '-';
    }

    // Update last activity
    if (lastActivityEl && lastActivityTime) {
      const elapsed = Math.floor((Date.now() - lastActivityTime) / 1000);
      lastActivityEl.textContent = elapsed < 60 ? `${elapsed} sec ago` : formatDuration(elapsed) + ' ago';
    } else if (lastActivityEl) {
      lastActivityEl.textContent = '-';
    }

    // Update ReadyState
    if (readyStateEl && socket) {
      readyStateEl.textContent = getReadyStateText(socket.readyState);
    } else if (readyStateEl) {
      readyStateEl.textContent = '-';
    }

    // Update connection attempts
    if (connectionAttemptsEl) {
      connectionAttemptsEl.textContent = connectionAttempts.toString();
    }

    // Update messages received
    if (messagesReceivedEl) {
      messagesReceivedEl.textContent = messagesReceived.toString();
    }

    // Update current task
    if (currentTaskEl) {
      const taskInput = document.getElementById('task');
      currentTaskEl.textContent = isResearchActive && taskInput && taskInput.value ?
        (taskInput.value.length > 30 ? taskInput.value.substring(0, 27) + '...' : taskInput.value) :
        '-';
    }
  }

  // Get socket status object
  const getSocketStatus = () => {
    if (!socket) {
      return {
        statusText: 'Disconnected',
        indicatorClass: 'disconnected'
      };
    }

    switch (socket.readyState) {
      case WebSocket.CONNECTING:
        return {
          statusText: 'Connecting',
          indicatorClass: 'connecting'
        };
      case WebSocket.OPEN:
        return {
          statusText: 'Connected',
          indicatorClass: 'connected'
        };
      case WebSocket.CLOSING:
        return {
          statusText: 'Closing',
          indicatorClass: 'connecting'
        };
      case WebSocket.CLOSED:
      default:
        return {
          statusText: 'Disconnected',
          indicatorClass: 'disconnected'
        };
    }
  }

  // Get readable text for WebSocket readyState
  const getReadyStateText = (readyState) => {
    switch (readyState) {
      case WebSocket.CONNECTING:
        return '0 (Connecting)';
      case WebSocket.OPEN:
        return '1 (Open)';
      case WebSocket.CLOSING:
        return '2 (Closing)';
      case WebSocket.CLOSED:
        return '3 (Closed)';
      default:
        return `${readyState} (Unknown)`;
    }
  }

  // Format duration in seconds to human-readable string
  const formatDuration = (seconds) => {
    if (seconds < 60) {
      return `${seconds} sec`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)} min ${seconds % 60} sec`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours} hr ${minutes} min`;
    }
  }

  // Load conversation history from cookie
  const loadConversationHistory = () => {
    try {
      const storedHistory = getCookie('conversationHistory');
      if (storedHistory && storedHistory.trim() !== '') {
        try {
          const parsedHistory = JSON.parse(storedHistory);
          if (Array.isArray(parsedHistory)) {
            conversationHistory = parsedHistory;
            console.debug('Loaded research history from storage:', conversationHistory);
            console.log('Loaded research history:', conversationHistory.length, 'items');
          } else {
            console.warn('History storage does not contain an array');
            conversationHistory = [];
            deleteCookie('conversationHistory');
          }
        } catch (jsonError) {
          console.error('Invalid JSON in history storage:', jsonError);
          conversationHistory = [];
          deleteCookie('conversationHistory');
        }
      } else {
        console.log('No research history found in storage');
        conversationHistory = [];
      }
    } catch (error) {
      console.error('Error loading research history from storage:', error);
      conversationHistory = [];
      // If JSON parsing fails, delete the corrupt cookie
      deleteCookie('conversationHistory');
    }

    // Force render after loading
    renderHistoryEntries();
  }

  // Save conversation history to cookie
  const saveConversationHistory = () => {
    try {
      if (conversationHistory.length === 0) {
        deleteCookie('conversationHistory');
        console.debug('No history to save, deleted storage');
        return;
      }

      // Only keep the last 20 entries
      let storageHistory = [...conversationHistory];
      if (storageHistory.length > 20) {
        storageHistory = storageHistory.slice(0, 20);
        console.debug('Trimmed history to last 20 entries');
      }

      // Only keep minimal fields: prompt, links and timestamp
      storageHistory = storageHistory.map(entry => ({
        prompt: entry.prompt || '',
        links: entry.links || {},
        timestamp: entry.timestamp || new Date().toISOString()
      }));

      const jsonString = JSON.stringify(storageHistory);
      console.debug('History JSON size:', jsonString.length, 'characters');

      setCookie('conversationHistory', jsonString, 30);

      if (storageHistory.length > 0 && !isInitialLoad) {
        showToast('Research history saved!');
      }
    } catch (error) {
      console.error('Error saving research history:', error);
      showToast('Error saving history. Some entries may not be saved.');
    }
  }

  // Delete a history entry
  const deleteHistoryEntry = (index) => {
    if (confirm('Are you sure you want to delete this research entry?')) {
      conversationHistory.splice(index, 1);
      saveConversationHistory();
      renderHistoryEntries();
      showToast('Entry deleted successfully');
    }
  }

  // Clear all conversation history
  const clearConversationHistory = () => {
    if (confirm('Are you sure you want to clear all research history? This cannot be undone.')) {
      conversationHistory = [];
      saveConversationHistory();
      renderHistoryEntries();
      showToast('Research history cleared successfully');
    }
  }

  // Filter history entries based on search term
  const filterHistoryEntries = () => {
    const searchTerm = document.getElementById('historySearch').value.toLowerCase();
    const historyEntries = document.getElementById('historyEntries');

    if (!historyEntries) return;

    const entries = historyEntries.querySelectorAll('.history-entry');

    entries.forEach(entry => {
      const title = entry.querySelector('.history-entry-title').textContent.toLowerCase();
      // Search only in the title since we no longer have preview text
      if (title.includes(searchTerm)) {
        entry.style.display = 'block';
      } else {
        entry.style.display = 'none';
      }
    });
  }

  // Sort history entries by timestamp
  const sortHistoryEntries = (order) => {
    conversationHistory.sort((a, b) => {
      // Default to newest first if timestamps don't exist
      if (!a.timestamp || !b.timestamp) return 0;

      if (order === 'newest') {
        return new Date(b.timestamp) - new Date(a.timestamp);
      } else {
        return new Date(a.timestamp) - new Date(b.timestamp);
      }
    });
  }

  // Render history entries in the panel
  const renderHistoryEntries = () => {
    const historyEntries = document.getElementById('historyEntries');
    if (!historyEntries) return;

    historyEntries.innerHTML = '';

    if (!conversationHistory || conversationHistory.length === 0) {
      historyEntries.innerHTML = '<p class="text-center mt-4 text-muted">No research history yet.</p>';
      return;
    }

    // Sort by the current selection
    const sortOrder = document.getElementById('historySortOrder')?.value || 'newest';
    sortHistoryEntries(sortOrder);
    console.debug('Sorted history entries:', sortOrder);

    conversationHistory.forEach((entry, index) => {
      const entryElement = document.createElement('div');
      entryElement.className = 'history-entry';
      entryElement.setAttribute('data-id', index);

      // Make the entire entry clickable to load it
      entryElement.addEventListener('click', () => {
        loadResearchEntry(index);
      });

      // Format timestamp if available
      let timestampHTML = '';
      if (entry.timestamp) {
        try {
          const timestamp = new Date(entry.timestamp);
          const formattedDate = timestamp.toLocaleDateString();
          const formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          timestampHTML = `<span class="history-entry-timestamp">${formattedDate} ${formattedTime}</span>`;
        } catch (e) {
          console.error('Error formatting timestamp:', e);
        }
      }

      // Make sure links object exists
      const links = entry.links || {};

      // Build the HTML for the entry with enhanced formatting
      entryElement.innerHTML = `
        <div class="history-entry-header">
          <h4 class="history-entry-title">${entry.prompt || 'Unnamed Research'}</h4>
          ${timestampHTML}
        </div>
        <div class="history-entry-format">
          ${links.pdf ? `<a href="${links.pdf}" class="history-entry-action" target="_blank" title="Open PDF Report"><i class="fas fa-file-pdf"></i> PDF</a>` : ''}
          ${links.docx ? `<a href="${links.docx}" class="history-entry-action" target="_blank" title="Open Word Document"><i class="fas fa-file-word"></i> Word</a>` : ''}
          ${links.md ? `<a href="${links.md}" class="history-entry-action" target="_blank" title="Open Markdown File"><i class="fas fa-file-lines"></i> MD</a>` : ''}
          ${links.json ? `<a href="${links.json}" class="history-entry-action" target="_blank" title="Open JSON Data"><i class="fas fa-file-code"></i> JSON</a>` : ''}
        </div>
        <div class="history-entry-actions">
          <button class="history-entry-action delete-entry" title="Delete this research entry"><i class="fas fa-trash-alt"></i></button>
        </div>
      `;

      // Add action button handlers
      const deleteBtn = entryElement.querySelector('.delete-entry');
      if (deleteBtn) {
        deleteBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          deleteHistoryEntry(index);
        });
      }

      historyEntries.appendChild(entryElement);
      setTimeout(() => {
        entryElement.style.animationDelay = `${index * 50}ms`;
      }, 0);
    });
  }

  // Load a research entry from history
  const loadResearchEntry = (index) => {
    const entry = conversationHistory[index];
    if (!entry) return;

    // Fill form with the entry data
    document.getElementById('task').value = entry.prompt; // Changed from entry.task for consistency
    
    // Check if report_type, report_source, and tone are in entry, otherwise use defaults or skip
    const reportTypeSelect = document.querySelector('select[name="report_type"]');
    if (reportTypeSelect && entry.reportType) {
        reportTypeSelect.value = entry.reportType;
    } else if (reportTypeSelect) {
        reportTypeSelect.value = reportTypeSelect.options[0].value; // Default to first option
    }

    const reportSourceSelect = document.querySelector('select[name="report_source"]');
    if (reportSourceSelect && entry.reportSource) {
        reportSourceSelect.value = entry.reportSource;
    } else if (reportSourceSelect) {
        reportSourceSelect.value = reportSourceSelect.options[0].value; // Default to first option
    }

    const toneSelect = document.querySelector('select[name="tone"]');
    if (toneSelect && entry.tone) {
        toneSelect.value = entry.tone;
    } else if (toneSelect) {
        toneSelect.value = toneSelect.options[0].value; // Default to first option
    }

    const queryDomainsInput = document.querySelector('input[name="query_domains"]');
    if (queryDomainsInput) {
        if (entry.queryDomains && Array.isArray(entry.queryDomains) && entry.queryDomains.length > 0) {
            queryDomainsInput.value = entry.queryDomains.join(', ');
        } else {
            queryDomainsInput.value = ''; // Clear if not present
        }
    }

    // Clear current research/report areas
    document.getElementById('output').innerHTML = '';
    document.getElementById('reportContainer').innerHTML = '';
    document.getElementById('selectedImagesContainer').innerHTML = '';
    document.getElementById('selectedImagesContainer').style.display = 'none';

    // Hide download bar and chat
    const stickyDownloadsBar = document.getElementById('stickyDownloadsBar');
    if (stickyDownloadsBar) {
        stickyDownloadsBar.classList.remove('visible');
    }
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer) {
        chatContainer.style.display = 'none';
    }

    // Reset UI state and report-specific buttons
    updateState('initial'); // This will hide copy buttons etc.

    // Close the history panel
    const historyPanel = document.getElementById('historyPanel');
    if (historyPanel) {
        historyPanel.classList.remove('open');
    }

    // Scroll to the form
    const formElement = document.getElementById('form');
    if (formElement) {
        formElement.scrollIntoView({ behavior: 'smooth' });
    }

    // Inform user
    showToast('Research parameters loaded. You can start the research again.');
  }

  // Copy entry content to clipboard
  const copyEntryToClipboard = (index) => {
    const entry = conversationHistory[index];
    if (!entry || !entry.content) return;

    const textarea = document.createElement('textarea');
    textarea.value = entry.content;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);

    // Show a toast notification
    showToast('Research content copied to clipboard!');
  }

  // Show a toast notification
  const showToast = (message, duration = 3000) => {
    // Create toast element if it doesn't exist
    let toast = document.getElementById('toast-notification');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'toast-notification';
      toast.className = 'toast-notification';
      document.body.appendChild(toast);
    }

    // Set message and show
    toast.textContent = message;
    toast.classList.add('show');

    // Hide after specified duration
    setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  }

  // Save current research to history (minimal: prompt and links only)
  const saveToHistory = (report, downloadLinks) => {
    if (!downloadLinks) {
      console.error('No download links provided');
      showToast('Error: Could not save research to history');
      return;
    }

    const prompt = document.getElementById('task').value;

    // Create links object with proper structure
    const links = {
      pdf: downloadLinks.pdf || '',
      docx: downloadLinks.docx || '',
      md: downloadLinks.md || '',
      json: downloadLinks.json || ''
    };

    console.debug('Saving history with links:', links);

    // Create history entry with timestamp
    const historyEntry = {
      prompt,
      links,
      timestamp: new Date().toISOString()
    };

    // Add to beginning of array if it's not empty
    if (!conversationHistory) {
      conversationHistory = [];
    }

    conversationHistory.unshift(historyEntry);
    saveConversationHistory();
    renderHistoryEntries();
    document.getElementById('historyPanel').classList.add('open');

    // Prompt user about storage method
    if (cookiesEnabled) {
      showToast('Research saved! Your history is stored in a browser cookie.');
    } else {
      showToast('Research saved! Your history is stored using localStorage.');
    }
  }

  // Function to update the research icon spinning state
  const updateResearchIcon = (isSpinning) => {
    const modernSpinner = document.getElementById('modernSpinner');
    if (modernSpinner) {
      if (isSpinning) {
        modernSpinner.classList.add('spinning');
      } else {
        modernSpinner.classList.remove('spinning');
      }
    }
  };

  const startResearch = () => {
    document.getElementById('output').innerHTML = ''
    document.getElementById('reportContainer').innerHTML = ''
    dispose_socket?.() // Call previous dispose function if it exists

    // Reset report variables
    allReports = '';
    currentReport = '';
    isFirstReport = true;

    // Hide the download bar
    const stickyDownloadsBar = document.getElementById('stickyDownloadsBar');
    if (stickyDownloadsBar) {
      stickyDownloadsBar.classList.remove('visible');
    }

    // Hide the chat container
    chatContainer = document.getElementById('chatContainer');
    if (chatContainer) {
      chatContainer.style.display = 'none';
    }

    const imageContainer = document.getElementById('selectedImagesContainer')
    imageContainer.innerHTML = ''
    imageContainer.style.display = 'none'

    updateState('in_progress')

    addAgentResponse({
      output: '🧙‍♂️ Gathering information and analyzing your research topic...',
    })

    // Scroll to the "Research Progress" section
    const researchOutputContainer = document.querySelector('.research-output-container');
    if (researchOutputContainer) {
        researchOutputContainer.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    dispose_socket = listenToSockEvents() // Assign the new dispose function
  }

  const listenToSockEvents = () => {
    const { protocol, host, pathname } = window.location
    const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'
      }//${host}${pathname}ws`

    // Set a timeout for connection - if it takes too long, stop the spinner
    connectionTimeout = setTimeout(() => {
      updateResearchIcon(false);
      console.log("WebSocket connection timed out");
    }, 10000); // 10 seconds timeout

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

    // Increment connection attempts counter
    connectionAttempts++;

    // Update WebSocket status
    updateWebSocketStatus();

    socket = new WebSocket(ws_uri)
    let reportContent = ''; // Store the report content for history
    let downloadLinkData = null; // Store download links

    socket.onmessage = (event) => {
      // Reset reconnect attempts on successful message
      reconnectAttempts = 0;

      const data = JSON.parse(event.data)
      console.log("Received message:", data);  // Debug log

      // Update WebSocket metrics
      messagesReceived++;
      lastActivityTime = Date.now();
      updateWebSocketStatus();

      if (data.type === 'logs') {
        addAgentResponse(data)
      } else if (data.type === 'images') {
        console.log("Received images:", data);  // Debug log
        displaySelectedImages(data)
      } else if (data.type === 'report') {
        // Add to reportContent for history
        reportContent += data.output;

        // Get the current report_type
        const report_type = document.querySelector('select[name="report_type"]').value;

        // Determine if we're using detailed_report
        const isDetailedReport = report_type === 'detailed_report';

        if (isDetailedReport) {
          allReports += data.output; // Accumulate raw markdown
          // Always render the HTML of *all accumulated markdown* for detailed reports during streaming.
          // writeReport will replace the container's content.
          writeReport({ output: allReports, type: 'report' }, converter, false, false);
        } else {
          // For all other report types, append HTML of current chunk to the container.
          writeReport({ output: data.output, type: 'report' }, converter, false, true); // append = true
        }
      } else if (data.type === 'path') {
        updateState('finished')
        downloadLinkData = updateDownloadLink(data)
        isResearchActive = false;

        // Get the current report_type
        const report_type = document.querySelector('select[name="report_type"]').value;

        // Only for detailed_report, show the complete accumulated report at the end
        if (report_type === 'detailed_report' && allReports) {
          const finalData = { output: allReports, type: 'report' };
          writeReport(finalData, converter, true, false); // isFinal=true, append=false
        }

        // Save to history now that research is complete
        if (reportContent && downloadLinkData) {
          saveToHistory(reportContent, downloadLinkData);

          // Reset variables for next research session
          reportContent = '';
          allReports = '';
          currentReport = '';
          isFirstReport = true;
        }

        // Update WebSocket status
        updateWebSocketStatus();
      } else if (data.type === 'chat') {
        // Handle chat messages from the AI
        // Remove loading indicator and add AI's response
        const loadingElements = document.querySelectorAll('.chat-loading');
        if (loadingElements.length > 0) {
          loadingElements[loadingElements.length - 1].remove();
        }

        // Add AI message to chat
        if (data.content) {
          addChatMessage(data.content, false);
        }
      }
    }

    socket.onopen = (event) => {
      // Clear the connection timeout
      clearTimeout(connectionTimeout);

      // Update WebSocket metrics
      connectionStartTime = Date.now();
      lastActivityTime = Date.now();
      updateWebSocketStatus();

      // Reset reconnect attempts on successful connection
      reconnectAttempts = 0;

      // Ensure the research icon is spinning when connection is established
      updateResearchIcon(true);

      // If this is a reconnection and we're in research mode, don't send a new start command
      if (isResearchActive && lastRequestData) {
        console.log("Reconnected during active research, not sending new start command");
        return;
      }

      const task = document.getElementById('task').value
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

      const query_domains_str = document.querySelector('input[name="query_domains"]').value
      let query_domains = []
      if (query_domains_str) {
        query_domains = query_domains_str.split(',')
          .map((domain) => domain.trim())
          .filter((domain) => domain.length > 0);
      }

      const requestData = {
        task: task,
        report_type: report_type,
        report_source: report_source,
        source_urls: source_urls,
        tone: tone,
        agent: agent,
        query_domains: query_domains,
      }

      // Add MCP configuration if enabled
      const mcpData = collectMCPData();
      if (mcpData) {
        Object.assign(requestData, mcpData);
        console.log('Including MCP configuration:', mcpData);
      }

      // Store the request data for potential reconnection
      lastRequestData = requestData;

      socket.send(`start ${JSON.stringify(requestData)}`)
    }

    socket.onclose = (event) => {
      // Update metrics and status when connection closes
      connectionStartTime = null;
      updateWebSocketStatus();

      console.log("WebSocket connection closed", event);

      // If research is active, try to automatically reconnect
      if (isResearchActive) {
        reconnectWebSocket();
      }
    }

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      updateWebSocketStatus();
    }

    // return dispose function
    return () => {
      try {
        isResearchActive = false; // Mark research as inactive
        if (socket && socket.readyState !== WebSocket.CLOSED && socket.readyState !== WebSocket.CLOSING) {
          socket.close();
        }

        // Update metrics on socket disposal
        connectionStartTime = null;
        updateWebSocketStatus();
      } catch (e) {
        console.error('Error closing socket:', e)
      }
    };
  }

  const addAgentResponse = (data) => {
    const output = document.getElementById('output');
    const responseDiv = document.createElement('div');
    responseDiv.className = 'agent_response';
    responseDiv.innerHTML = data.output; // Assuming data.output is safe HTML or simple text from agent
    output.appendChild(responseDiv);
    output.scrollTop = output.scrollHeight;
    output.style.display = 'block';
  }

  const writeReport = (data, converter, isFinal = false, append = false) => {
    const reportContainer = document.getElementById('reportContainer');

    // Convert markdown to HTML
    const markdownOutput = converter.makeHtml(data.output);

    // If this is the final report or we should append
    if (isFinal) {
      // For final reports, always replace content
      reportContainer.innerHTML = markdownOutput;
    } else if (append) {
      // Append mode - add to existing content
      reportContainer.innerHTML += markdownOutput;
    } else {
      // Replace mode - overwrite existing content
      reportContainer.innerHTML = markdownOutput;
    }

    // Auto-scroll to the bottom of the container
    reportContainer.scrollTop = reportContainer.scrollHeight;
  }

  const updateDownloadLink = (data) => {
    if (!data.output) {
      console.error('No output data received');
      return;
    }

    const { pdf, docx, md, json } = data.output;
    console.log('Received paths:', { pdf, docx, md, json });

    // Store these links for history
    const currentLinks = { pdf, docx, md, json };

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

    // Update links in sticky download bar
    updateLink('downloadLink', pdf);
    updateLink('downloadLinkWord', docx);
    updateLink('downloadLinkMd', md);
    updateLink('downloadLinkJson', json);

    // Update duplicate buttons above the report
    updateLink('downloadLinkTop', pdf);
    updateLink('downloadLinkWordTop', docx);
    updateLink('downloadLinkMdTop', md);
    updateLink('downloadLinkJsonTop', json);

    // Make sure download buttons are visible when download links are ready
    showDownloadPanels();

    // Return links for history saving
    return currentLinks;
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

    // Show a temporary success message with icon change and toast notification
    const copyBtn = document.getElementById('copyToClipboard');
    const copyBtnTop = document.getElementById('copyToClipboardTop');

    // Function to reset the icon for both buttons
    const resetIcons = () => {
      if (copyBtn) {
        copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
      }
      if (copyBtnTop) {
        copyBtnTop.innerHTML = '<i class="fas fa-copy"></i>';
      }
    };

    // Change to green check mark
    if (copyBtn) {
      copyBtn.innerHTML = '<i class="fas fa-check" style="color: green;"></i> Copied!';
    }
    if (copyBtnTop) {
      copyBtnTop.innerHTML = '<i class="fas fa-check" style="color: green;"></i>';
    }

    // Show toast notification
    showToast('Copied to clipboard!');

    // Reset the button after 3 seconds
    setTimeout(resetIcons, 3000);
  }

  const updateState = (state) => {
    var status = ''
    switch (state) {
      case 'in_progress':
        status = 'Research in progress...'
        setReportActionsStatus('disabled')
        isResearchActive = true;
        // Make the research icon spin
        updateResearchIcon(true);
        // Hide chat container during research
        chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
          chatContainer.style.display = 'none';
        }
        // Hide the copy button in the header
        const copyBtnTop = document.getElementById('copyToClipboardTop');
        if (copyBtnTop) {
          copyBtnTop.style.display = 'none';
        }
        // Hide the JSON button container
        const jsonContainer = document.getElementById('jsonButtonContainer');
        if (jsonContainer) {
          jsonContainer.style.display = 'none';
        }
        break
      case 'finished':
        status = 'Research finished!'
        setReportActionsStatus('enabled')
        isResearchActive = false;
        // Stop the research icon spinning
        updateResearchIcon(false);

        // Show download panels and hide feature panels when research is finished
        showDownloadPanels();

        // Enable the copy button
        const copyButton = document.getElementById('copyToClipboard');
        if (copyButton) {
          copyButton.classList.remove('disabled');
        }

        // Show copy button in the header
        const topCopyButton = document.getElementById('copyToClipboardTop');
        if (topCopyButton) {
          topCopyButton.style.display = 'inline-block';
          topCopyButton.addEventListener('click', copyToClipboard);
        }

        // Show JSON button container
        const jsonButtonContainer = document.getElementById('jsonButtonContainer');
        if (jsonButtonContainer) {
          jsonButtonContainer.style.display = 'block';
        }

        // Show chat container when research is finished
        chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
          chatContainer.style.display = 'block';
          // Initialize chat if not already initialized
          initChat();
        }
        break
      case 'error':
        status = 'Research failed!'
        setReportActionsStatus('disabled')
        isResearchActive = false;
        // Stop the research icon spinning
        updateResearchIcon(false);
        break
      case 'initial':
        status = ''
        setReportActionsStatus('hidden')
        isResearchActive = false;
        // Make sure the research icon is not spinning initially
        updateResearchIcon(false);
        // Hide the copy button in the header
        const initialCopyBtnTop = document.getElementById('copyToClipboardTop');
        if (initialCopyBtnTop) {
          initialCopyBtnTop.style.display = 'none';
        }
        // Hide the JSON button container
        const initialJsonContainer = document.getElementById('jsonButtonContainer');
        if (initialJsonContainer) {
          initialJsonContainer.style.display = 'none';
        }
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
    let dialog = document.querySelector('.image-dialog');
    if (!dialog) {
        dialog = document.createElement('div');
        dialog.className = 'image-dialog';

        const img = document.createElement('img');
        img.alt = 'Full-size Research Image';

        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'Close';
        closeBtn.className = 'close-btn'; // Added class for styling

        dialog.appendChild(img);
        dialog.appendChild(closeBtn);
        document.body.appendChild(dialog);

        closeBtn.onclick = () => {
            dialog.classList.remove('visible');
        };
        // Close on clicking backdrop
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                dialog.classList.remove('visible');
            }
        });
    }

    const imgElement = dialog.querySelector('img');
    imgElement.src = imageUrl;
    dialog.classList.add('visible');

    // Close with Escape key
    const escapeKeyListener = (e) => {
        if (e.key === 'Escape') {
            dialog.classList.remove('visible');
            document.removeEventListener('keydown', escapeKeyListener);
        }
    };
    document.addEventListener('keydown', escapeKeyListener);
}

  // Function to show download bar and enable buttons
  const showDownloadPanels = () => {
    // Show the bar by adding the visible class
    const stickyDownloadsBar = document.getElementById('stickyDownloadsBar');
    if (stickyDownloadsBar) {
      stickyDownloadsBar.classList.add('visible');
    }

    // Enable all download buttons
    const downloadButtons = document.querySelectorAll('.download-option-btn, .report-action-btn');
    downloadButtons.forEach(button => {
      button.classList.remove('disabled');
    });

    // Make top buttons report-actions section visible
    const reportActions = document.querySelector('.report-actions');
    if (reportActions) {
      reportActions.style.display = 'flex';
    }
  }

  // --- Storage Helpers (Cookies or LocalStorage) ---
  function setCookie(name, value, days) {
    // Maximum cookie size is around 4KB (4096 bytes)
    const MAX_COOKIE_SIZE = 4000;

    // If cookies are disabled, use localStorage instead
    if (!cookiesEnabled) {
      try {
        localStorage.setItem(name, value);
        console.debug(`Data saved to localStorage: ${name}`);
        return true;
      } catch (e) {
        console.error("Error saving to localStorage:", e);
        return false;
      }
    }

    let expires = '';
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = '; expires=' + date.toUTCString();
    }

    // Encode the value
    const encodedValue = encodeURIComponent(value);

    // Calculate cookie size
    const cookieSize = (name + '=' + encodedValue + expires + '; path=/').length;
    console.debug(`Setting cookie: ${name}, size: ${cookieSize} bytes`);

    // If cookie is too large, display warning and truncate history
    if (cookieSize > MAX_COOKIE_SIZE) {
      console.warn(`Cookie size (${cookieSize} bytes) exceeds the ${MAX_COOKIE_SIZE} bytes limit!`);
      showToast('Warning: History too large for cookie storage! Oldest entries will be removed.');

      if (name === 'conversationHistory') {
        try {
          // Parse, reduce entries, and try again
          const historyData = JSON.parse(value);
          if (Array.isArray(historyData) && historyData.length > 1) {
            // Remove the last entry and try again recursively
            const reducedHistory = historyData.slice(0, -1);
            console.debug(`Reducing history from ${historyData.length} to ${reducedHistory.length} entries`);
            setCookie(name, JSON.stringify(reducedHistory), days);
            return; // Exit after recursive call
          }
        } catch (e) {
          console.error('Could not parse history to reduce size:', e);
        }
      }

      return false; // Indicate failure
    }

    // Set the cookie
    document.cookie = name + '=' + encodedValue + expires + '; path=/';
    console.debug(`Cookie set: ${name}`);
    return true; // Indicate success
  }

  function getCookie(name) {
    console.debug(`Getting data: ${name}`);

    // If cookies are disabled, use localStorage instead
    if (!cookiesEnabled) {
      try {
        const value = localStorage.getItem(name);
        if (value) {
          console.debug(`Data found in localStorage: ${name}, length: ${value.length} chars`);
          return value;
        }
        console.debug(`Data not found in localStorage: ${name}`);
        return null;
      } catch (e) {
        console.error("Error retrieving from localStorage:", e);
        return null;
      }
    }

    const nameEQ = name + '=';
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) == 0) {
        const value = decodeURIComponent(c.substring(nameEQ.length, c.length));
        console.debug(`Found cookie: ${name}, length: ${value.length} chars`);
        return value;
      }
    }
    console.debug(`Cookie not found: ${name}`);
    return null;
  }

  function deleteCookie(name) {
    console.debug(`Deleting storage: ${name}`);

    // If cookies are disabled, use localStorage instead
    if (!cookiesEnabled) {
      try {
        localStorage.removeItem(name);
        return;
      } catch (e) {
        console.error("Error removing from localStorage:", e);
        return;
      }
    }

    document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  }
  // --- End Storage Helpers ---

  // Debug Helper - check cookie status
  const checkCookieStatus = () => {
    if (!cookiesEnabled) {
      const storageData = localStorage.getItem('conversationHistory');
      if (storageData) {
        const byteSize = new Blob([storageData]).size;
        const kilobyteSize = (byteSize / 1024).toFixed(2);

        try {
          const parsed = JSON.parse(storageData);
          const entryCount = Array.isArray(parsed) ? parsed.length : 0;

          showToast(`Using localStorage: ${kilobyteSize}KB, ${entryCount} entries`);
          console.debug(`LocalStorage size: ${byteSize} bytes, ${kilobyteSize}KB`);
          console.debug(`LocalStorage entries: ${entryCount}`);
        } catch (e) {
          showToast(`LocalStorage contains invalid data: ${kilobyteSize}KB`);
          console.error('LocalStorage parse error:', e);
        }
      } else {
        showToast('No research history found in localStorage');
      }
      return;
    }

    const allCookies = document.cookie;
    console.debug('All cookies:', allCookies);

    const conversationCookie = getCookie('conversationHistory');
    if (conversationCookie) {
      const byteSize = new Blob([conversationCookie]).size;
      const kilobyteSize = (byteSize / 1024).toFixed(2);

      try {
        const parsed = JSON.parse(conversationCookie);
        const entryCount = Array.isArray(parsed) ? parsed.length : 0;

        showToast(`Cookie found: ${kilobyteSize}KB, ${entryCount} research entries`);
        console.debug(`Cookie size: ${byteSize} bytes, ${kilobyteSize}KB`);
        console.debug(`Cookie entries: ${entryCount}`);
      } catch (e) {
        showToast(`Cookie found but invalid: ${kilobyteSize}KB`);
        console.error('Cookie parse error:', e);
      }
    } else {
      showToast('No research history cookie found');
    }
  }

  // Export history to a downloadable JSON file
  const exportHistory = () => {
    try {
      if (!conversationHistory || conversationHistory.length === 0) {
        showToast('No research history to export');
        return;
      }

      // Create a formatted JSON string with pretty-printing
      const historyJson = JSON.stringify(conversationHistory, null, 2);

      // Create a Blob containing the data
      const blob = new Blob([historyJson], { type: 'application/json' });

      // Create an object URL for the blob
      const url = URL.createObjectURL(blob);

      // Create a temporary link element
      const link = document.createElement('a');
      link.href = url;

      // Set download attribute with filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      link.download = `research-history-${timestamp}.json`;

      // Append to the document
      document.body.appendChild(link);

      // Programmatically click the link to trigger the download
      link.click();

      // Clean up
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      showToast('Research history exported to JSON file');
      console.debug('History exported, entries:', conversationHistory.length);
    } catch (error) {
      console.error('Error exporting history:', error);
      showToast('Error exporting research history');
    }
  }

  // Trigger the file input for importing history
  const triggerImportHistory = () => {
    const fileInput = document.getElementById('historyFileInput');
    if (fileInput) {
      fileInput.click();
    } else {
      showToast('Import functionality not available');
    }
  }

  // Handle the file import for history
  const handleFileImport = (event) => {
    const file = event.target.files[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target.result;
        const importedData = JSON.parse(content);

        // Validate the imported data
        if (!Array.isArray(importedData)) {
          throw new Error('Imported data is not an array');
        }

        // Check if each entry has the required fields
        const validEntries = importedData.filter(entry => {
          return entry &&
            typeof entry === 'object' &&
            (entry.prompt || entry.task) && // Allow both prompt and legacy task field
            (entry.links || entry.downloadLinks); // Allow both links and legacy downloadLinks
        });

        if (validEntries.length === 0) {
          showToast('No valid research entries found in the imported file');
          return;
        }

        // Map the entries to the current structure if needed
        const mappedEntries = validEntries.map(entry => {
          return {
            prompt: entry.prompt || entry.task || '',
            links: entry.links || entry.downloadLinks || {},
            timestamp: entry.timestamp || new Date().toISOString()
          };
        });

        // Confirm before overwriting existing history
        if (conversationHistory && conversationHistory.length > 0) {
          if (confirm(`You have ${conversationHistory.length} existing research entries. Do you want to:
- Click OK to MERGE imported history with existing history
- Click Cancel to REPLACE all existing history with imported data`)) {
            // Merge with existing history
            conversationHistory = [...mappedEntries, ...conversationHistory];
          } else {
            // Replace existing history
            conversationHistory = mappedEntries;
          }
        } else {
          // No existing history, just set the imported data
          conversationHistory = mappedEntries;
        }

        // Save the new history and update the UI
        saveConversationHistory();
        renderHistoryEntries();

        showToast(`Successfully imported ${validEntries.length} research entries`);
        console.debug('Research history imported, valid entries:', validEntries.length);

      } catch (error) {
        console.error('Error importing history:', error);
        showToast('Error importing research history: Invalid file format');
      }

      // Reset the file input so the same file can be selected again
      event.target.value = '';
    };

    reader.onerror = () => {
      console.error('Error reading file');
      showToast('Error reading the imported file');
      event.target.value = '';
    };

    reader.readAsText(file);
  }

  // Initialize chat functionality
  const initChat = () => {
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const voiceInputBtn = document.getElementById('voiceInputBtn');

    if (!chatInput || !sendChatBtn) return;

    // Clear previous messages
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
      chatMessages.innerHTML = '';
    }

    // Add event listeners for chat input
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });

    sendChatBtn.addEventListener('click', sendChatMessage);

    // Initialize speech recognition if supported
    if (voiceInputBtn) {
      initSpeechRecognition(voiceInputBtn, chatInput);
    }

    // Auto-resize textarea as content grows
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = (chatInput.scrollHeight) + 'px';
    });

    // Add welcome message
    addChatMessage('I can answer questions about the research report. What would you like to know?', false);
  }

  // Initialize speech recognition
  const initSpeechRecognition = (button, inputElement) => {
    // Check if browser supports speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn('Speech recognition not supported in this browser');
      button.style.display = 'none';
      return;
    }

    const recognition = new SpeechRecognition();

    // Configure speech recognition
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let isListening = false;
    let finalTranscript = '';

    // Add event listeners for speech recognition
    recognition.onstart = () => {
      isListening = true;
      finalTranscript = '';
      button.classList.add('listening');
      button.innerHTML = '<i class="fas fa-microphone-slash"></i>';
      button.title = 'Stop listening';

      // Show visual feedback
      showToast('Listening...', 1000);
    };

    recognition.onresult = (event) => {
      let interimTranscript = '';

      // Loop through the results
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      // Update the input element with the transcription
      inputElement.value = finalTranscript + interimTranscript;

      // Trigger input event to resize textarea
      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      resetRecognition();

      if (event.error === 'not-allowed') {
        showToast('Microphone access denied. Please allow microphone access in your browser settings.', 3000);
      } else {
        showToast('Speech recognition error: ' + event.error, 3000);
      }
    };

    recognition.onend = () => {
      resetRecognition();
    };

    // Reset the recognition state
    const resetRecognition = () => {
      isListening = false;
      button.classList.remove('listening');
      button.innerHTML = '<i class="fas fa-microphone"></i>';
      button.title = 'Use voice input';
    };

    // Toggle speech recognition on button click
    button.addEventListener('click', () => {
      if (isListening) {
        recognition.stop();
      } else {
        recognition.start();
      }
    });
  };

  // Create a new function to handle WebSocket reconnection
  const reconnectWebSocket = (message = null) => {
    // Don't attempt too many reconnections
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error(`Failed to reconnect after ${maxReconnectAttempts} attempts`);
      addChatMessage(`Unable to reconnect after ${maxReconnectAttempts} attempts. Please refresh the page.`, false);
      return false;
    }

    reconnectAttempts++;

    // Calculate backoff time (exponential backoff)
    const backoff = reconnectInterval * Math.pow(1.5, reconnectAttempts - 1);
    console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts}) in ${backoff}ms...`);

    // Show reconnection status to user
    addChatMessage(`Connection lost. Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`, false);

    // Try to reconnect after delay
    setTimeout(() => {
      try {
        // Setup new WebSocket connection
        dispose_socket = listenToSockEvents();

        // Set up a one-time handler to send the message after reconnection
        if (message) {
          const messageToSend = message;
          const checkConnectionAndSend = () => {
            if (socket && socket.readyState === WebSocket.OPEN) {
              console.log("Reconnected successfully, sending queued message");
              socket.send(messageToSend);
              return true;
            } else if (reconnectAttempts < maxReconnectAttempts) {
              console.log("Socket not ready yet, retrying...");
              setTimeout(checkConnectionAndSend, 1000);
              return false;
            }
            return false;
          };

          setTimeout(checkConnectionAndSend, 1000);
        }

        return true;
      } catch (e) {
        console.error("Error during reconnection:", e);
        return false;
      }
    }, backoff);

    return true;
  };

  // Send a chat message
  const sendChatMessage = () => {
    const chatInput = document.getElementById('chatInput');
    if (!chatInput || !chatInput.value.trim()) return;

    const message = chatInput.value.trim();

    // Add user message to chat
    addChatMessage(message, true);

    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Add loading indicator
    const loadingId = addLoadingIndicator();

    // Prepare the message to send
    const messageToSend = `chat ${JSON.stringify({ message: message })}`;

    // Send message through WebSocket
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(messageToSend);
    } else {
      // If socket is closed, try to reconnect
      removeLoadingIndicator(loadingId);

      // Reset reconnect attempts if this is a new chat session
      if (reconnectAttempts >= maxReconnectAttempts) {
        reconnectAttempts = 0;
      }

      // Attempt to reconnect and queue the message to be sent after reconnection
      if (!reconnectWebSocket(messageToSend)) {
        // If reconnection fails or max attempts reached
        addChatMessage('Unable to send message. Connection is unavailable.', false);
      }
    }
  }

  // Add a chat message to the UI
  const addChatMessage = (message, isUser = false) => {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const messageEl = document.createElement('div');
    messageEl.className = `chat-message ${isUser ? 'user-message' : 'ai-message'}`;

    // Process message for AI responses (convert markdown to HTML for AI messages)
    let processedMessage = message;
    if (!isUser) {
      // Use showdown for markdown conversion
      const converter = new showdown.Converter({
        ghCodeBlocks: true,
        tables: true,
        tasklists: true,
        openLinksInNewWindow: true
      });
      processedMessage = converter.makeHtml(message);
    }

    // Set message content
    messageEl.innerHTML = isUser ? escapeHtml(processedMessage) : processedMessage;

    // Add timestamp
    const timestampEl = document.createElement('div');
    timestampEl.className = 'chat-timestamp';
    const now = new Date();
    timestampEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    messageEl.appendChild(timestampEl);

    // Add to chat container
    chatMessages.appendChild(messageEl);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Add a loading indicator
  const addLoadingIndicator = () => {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return null;

    const loadingId = 'loading-' + Date.now();
    const loadingEl = document.createElement('div');
    loadingEl.className = 'chat-message ai-message chat-loading';
    loadingEl.id = loadingId;

    // Create the dots
    for (let i = 0; i < 3; i++) {
      const dot = document.createElement('div');
      dot.className = 'chat-dot';
      loadingEl.appendChild(dot);
    }

    chatMessages.appendChild(loadingEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return loadingId;
  }

  // Remove loading indicator
  const removeLoadingIndicator = (loadingId) => {
    if (!loadingId) return;

    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) {
      loadingEl.remove();
    }
  }

  // Escape HTML to prevent XSS in user messages
  const escapeHtml = (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Initialize expand buttons
  const initExpandButtons = () => {
    // Report container expand button
    const expandReportBtn = document.getElementById('expandReportBtn');
    if (expandReportBtn) {
      expandReportBtn.addEventListener('click', () => {
        const reportContainer = document.querySelector('.report-container');
        toggleExpand(reportContainer);
      });
    }

    // Chat container expand button
    const expandChatBtn = document.getElementById('expandChatBtn');
    if (expandChatBtn) {
      expandChatBtn.addEventListener('click', () => {
        const chatContainer = document.getElementById('chatContainer');
        toggleExpand(chatContainer);
      });
    }

    // Output container expand button
    const expandOutputBtn = document.getElementById('expandOutputBtn');
    if (expandOutputBtn) {
      expandOutputBtn.addEventListener('click', () => {
        const outputContainer = document.querySelector('.research-output-container');
        toggleExpand(outputContainer);
      });
    }

    // Close expanded view when ESC key is pressed
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const expandedElements = document.querySelectorAll('.expanded-view');
        expandedElements.forEach(el => {
          // Reset the button icon
          const button = el.querySelector('.expand-button i');
          if (button) {
            button.classList.remove('fa-compress-alt');
            button.classList.add('fa-expand-alt');
          }

          // Reset content container styles
          const contentContainers = el.querySelectorAll('#reportContainer, #output, #chatMessages');
          contentContainers.forEach(container => {
            if (container) {
              container.style.maxHeight = '';
            }
          });

          // Remove expanded-view class
          el.classList.remove('expanded-view');
        });
      }
    });
  }

  // Toggle expand mode for an element
  const toggleExpand = (element) => {
    if (!element) return;

    // Toggle expanded-view class
    element.classList.toggle('expanded-view');

    // Change button icon and title based on state
    const buttonIcon = element.querySelector('.expand-button i');
    const button = element.querySelector('.expand-button');

    if (buttonIcon && button) {
      if (element.classList.contains('expanded-view')) {
        buttonIcon.classList.remove('fa-compress-alt');
        buttonIcon.classList.add('fa-compress-alt');
        button.title = 'Collapse'; // Update title to Collapse

        // Find content containers and expand their height
        const contentContainers = element.querySelectorAll('#reportContainer, #output, #chatMessages');
        contentContainers.forEach(container => {
          if (container) {
            // Set expanded heights - no positioning changes
            if (container.id === 'reportContainer') {
              container.style.maxHeight = '800px'; // Fixed expanded height for report
            } else {
              container.style.maxHeight = '600px'; // Fixed expanded height for other content
            }
          }
        });
      } else {
        buttonIcon.classList.remove('fa-compress-alt');
        buttonIcon.classList.add('fa-expand-alt');
        button.title = 'Expand'; // Update title to Expand

        // Reset heights back to original when collapsed
        const contentContainers = element.querySelectorAll('#reportContainer, #output, #chatMessages');
        contentContainers.forEach(container => {
          if (container) {
            container.style.maxHeight = '';
          }
        });
      }
    }
  }

  // MCP Configuration Management
  
  // Initialize MCP functionality
  const initMCPSection = () => {
    const mcpEnabled = document.getElementById('mcpEnabled');
    const mcpConfigSection = document.getElementById('mcpConfigSection');
    const mcpInfoBtn = document.getElementById('mcpInfoBtn');
    const mcpConfig = document.getElementById('mcpConfig');
    const mcpFormatBtn = document.getElementById('mcpFormatBtn');
    const mcpExampleLink = document.getElementById('mcpExampleLink');

    if (!mcpEnabled || !mcpConfigSection) {
      console.warn('MCP elements not found');
      return;
    }

    // Toggle MCP config section
    mcpEnabled.addEventListener('change', () => {
      if (mcpEnabled.checked) {
        mcpConfigSection.style.display = 'block';
        updateRetrieverForMCP(true);
      } else {
        mcpConfigSection.style.display = 'none';
        updateRetrieverForMCP(false);
      }
    });

    // MCP info modal
    if (mcpInfoBtn) {
      mcpInfoBtn.addEventListener('click', showMCPInfo);
    }

    // JSON validation and formatting
    if (mcpConfig) {
      mcpConfig.addEventListener('input', validateMCPConfig);
      mcpConfig.addEventListener('blur', validateMCPConfig);
    }

    if (mcpFormatBtn) {
      mcpFormatBtn.addEventListener('click', formatMCPConfig);
    }

    if (mcpExampleLink) {
      mcpExampleLink.addEventListener('click', (e) => {
        e.preventDefault();
        showMCPExample();
      });
    }

    // Preset buttons
    const presetButtons = document.querySelectorAll('.preset-btn');
    presetButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const preset = e.currentTarget.dataset.preset;
        addMCPPreset(preset);
      });
    });

    // Create MCP info modal
    createMCPInfoModal();

    // Initial validation
    validateMCPConfig();
  };

  // Validate MCP JSON configuration
  const validateMCPConfig = () => {
    const mcpConfig = document.getElementById('mcpConfig');
    const mcpConfigStatus = document.getElementById('mcpConfigStatus');
    
    if (!mcpConfig || !mcpConfigStatus) return;

    const configText = mcpConfig.value.trim();
    
    if (!configText || configText === '[]') {
      mcpConfig.className = 'form-control mcp-config-textarea';
      mcpConfigStatus.textContent = 'Empty configuration';
      mcpConfigStatus.className = 'mcp-status-text';
      return true;
    }

    try {
      const parsed = JSON.parse(configText);
      
      if (!Array.isArray(parsed)) {
        throw new Error('Configuration must be an array');
      }

      // Validate each server config
      const errors = [];
      parsed.forEach((server, index) => {
        if (!server.name) {
          errors.push(`Server ${index + 1}: missing name`);
        }
        if (!server.command && !server.connection_url) {
          errors.push(`Server ${index + 1}: missing command or connection_url`);
        }
      });

      if (errors.length > 0) {
        throw new Error(errors.join('; '));
      }

      mcpConfig.className = 'form-control mcp-config-textarea valid';
      mcpConfigStatus.textContent = `Valid JSON ✓ (${parsed.length} server${parsed.length !== 1 ? 's' : ''})`;
      mcpConfigStatus.className = 'mcp-status-text valid';
      return true;

    } catch (error) {
      mcpConfig.className = 'form-control mcp-config-textarea invalid';
      mcpConfigStatus.textContent = `Invalid JSON: ${error.message}`;
      mcpConfigStatus.className = 'mcp-status-text invalid';
      return false;
    }
  };

  // Format MCP JSON configuration
  const formatMCPConfig = () => {
    const mcpConfig = document.getElementById('mcpConfig');
    if (!mcpConfig) return;

    try {
      const parsed = JSON.parse(mcpConfig.value.trim() || '[]');
      mcpConfig.value = JSON.stringify(parsed, null, 2);
      validateMCPConfig();
      showToast('JSON formatted successfully!');
    } catch (error) {
      showToast('Cannot format invalid JSON');
    }
  };

  // Show MCP configuration example
  const showMCPExample = () => {
    const exampleConfig = [
      {
        "name": "github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
        }
      },
      {
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"],
        "env": {}
      }
    ];

    const mcpConfig = document.getElementById('mcpConfig');
    if (mcpConfig) {
      mcpConfig.value = JSON.stringify(exampleConfig, null, 2);
      validateMCPConfig();
      showToast('Example configuration loaded!');
    }
  };

  // Update retriever configuration for MCP
  const updateRetrieverForMCP = (enableMCP) => {
    if (enableMCP) {
      showToast('MCP enabled - will be included in research process');
    } else {
      showToast('MCP disabled - using web search only');
    }
  };

  // Show MCP information modal
  const showMCPInfo = () => {
    const modal = document.getElementById('mcpInfoModal');
    if (modal) {
      modal.classList.add('visible');
    }
  };

  // Create MCP info modal
  const createMCPInfoModal = () => {
    if (document.getElementById('mcpInfoModal')) return;

    const modal = document.createElement('div');
    modal.id = 'mcpInfoModal';
    modal.className = 'mcp-info-modal';
    
    modal.innerHTML = `
      <div class="mcp-info-content">
        <button class="mcp-info-close" onclick="closeMCPInfo()">
          <i class="fas fa-times"></i>
        </button>
        <h3>Model Context Protocol (MCP)</h3>
        <p>MCP enables GPT Researcher to connect with external tools and data sources through a standardized protocol.</p>
        
        <h4 class="highlight">Benefits:</h4>
        <ul>
          <li><span class="highlight">Access Local Data:</span> Connect to databases, file systems, and APIs</li>
          <li><span class="highlight">Use External Tools:</span> Integrate with web services and third-party tools</li>
          <li><span class="highlight">Extend Capabilities:</span> Add custom functionality through MCP servers</li>
          <li><span class="highlight">Maintain Security:</span> Controlled access with proper authentication</li>
        </ul>

        <h4 class="highlight">Quick Start:</h4>
        <ul>
          <li>Enable MCP using the checkbox above</li>
          <li>Click a preset to add pre-configured servers to the JSON</li>
          <li>Or paste your own MCP configuration as a JSON array</li>
          <li>Start your research - MCP will run with optimal settings</li>
        </ul>

        <h4 class="highlight">Configuration Format:</h4>
        <p>Each MCP server should be a JSON object with these properties:</p>
        <ul>
          <li><span class="highlight">name:</span> Unique identifier (e.g., "github", "filesystem")</li>
          <li><span class="highlight">command:</span> Command to run the server (e.g., "npx", "python")</li>
          <li><span class="highlight">args:</span> Array of arguments (e.g., ["-y", "@modelcontextprotocol/server-github"])</li>
          <li><span class="highlight">env:</span> Object with environment variables (e.g., {"API_KEY": "your_key"})</li>
        </ul>
      </div>
    `;

    document.body.appendChild(modal);

    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('visible');
      }
    });

    // Close with Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('visible')) {
        modal.classList.remove('visible');
      }
    });
  };

  // Close MCP info modal
  window.closeMCPInfo = () => {
    const modal = document.getElementById('mcpInfoModal');
    if (modal) {
      modal.classList.remove('visible');
    }
  };

  // Add MCP preset configurations
  const addMCPPreset = (preset) => {
    const presets = {
      github: {
        "name": "github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
        }
      },
      tavily: {
        "name": "tavily",
        "command": "npx",
        "args": ["-y", "tavily-mcp@0.1.2"],
        "env": {
          "TAVILY_API_KEY": "your_tavily_api_key_here"
        }
      },
      filesystem: {
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"],
        "env": {}
      }
    };

    const config = presets[preset];
    if (!config) return;

    const mcpConfig = document.getElementById('mcpConfig');
    if (!mcpConfig) return;

    try {
      let currentConfig = [];
      const currentText = mcpConfig.value.trim();
      
      if (currentText && currentText !== '[]') {
        currentConfig = JSON.parse(currentText);
      }

      // Check if server already exists
      const existingIndex = currentConfig.findIndex(server => server.name === config.name);
      
      if (existingIndex !== -1) {
        // Replace existing server
        currentConfig[existingIndex] = config;
        showToast(`Updated ${preset} MCP server configuration`);
      } else {
        // Add new server
        currentConfig.push(config);
        showToast(`Added ${preset} MCP server configuration`);
      }

      mcpConfig.value = JSON.stringify(currentConfig, null, 2);
      validateMCPConfig();

    } catch (error) {
      console.error('Error adding preset:', error);
      showToast('Error adding preset configuration');
    }
  };

  // Collect MCP configuration data
  const collectMCPData = () => {
    const mcpEnabled = document.getElementById('mcpEnabled');
    if (!mcpEnabled || !mcpEnabled.checked) {
      return null;
    }

    const mcpConfig = document.getElementById('mcpConfig');
    
    if (!mcpConfig) {
      console.warn('MCP config element not found for data collection');
      return null;
    }

    // Validate configuration before collecting
    if (!validateMCPConfig()) {
      showToast('Invalid MCP configuration - please fix errors before submitting');
      return null;
    }

    try {
      const configText = mcpConfig.value.trim();
      const mcpConfigs = configText && configText !== '[]' ? JSON.parse(configText) : [];

      return {
        mcp_enabled: true,
        mcp_strategy: "fast", // Always use "fast" strategy as default
        mcp_configs: mcpConfigs
      };
    } catch (error) {
      console.error('Error collecting MCP data:', error);
      showToast('Error processing MCP configuration');
      return null;
    }
  };

  return {
    init,
    startResearch,
    addTag,
    copyToClipboard,
    displaySelectedImages,
    showImageDialog,
    checkCookieStatus,
    exportHistory,
    importHistory: triggerImportHistory,  // Add import function to return object
    initChat,
    sendChatMessage,
    addChatMessage
  }
})()

window.addEventListener('DOMContentLoaded', GPTResearcher.init)
