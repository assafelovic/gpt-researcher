// Toggle advanced options
function toggleAdvanced() {
    const advancedSection = document.getElementById('advancedSection');
    const isChecked = document.getElementById('advancedToggle').checked;
    advancedSection.classList.toggle('visible', isChecked);
}

// Handle tag inputs (for URLs and domains)
function setupTagInput(containerId, hiddenInputId) {
    const container = document.getElementById(containerId);
    const input = container.querySelector('input');
    const hiddenInput = document.getElementById(hiddenInputId);
    const tags = new Set();
    
    function updateHiddenInput() {
        hiddenInput.value = Array.from(tags).join(',');
    }
    
    function addTag(value) {
        if (!value) return;
        tags.add(value);
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            ${value}
            <span class="tag-remove" onclick="this.parentElement.remove();tags.delete('${value}');updateHiddenInput();">×</span>
        `;
        container.insertBefore(tag, input);
        input.value = '';
        updateHiddenInput();
    }
    
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            addTag(input.value.trim());
        }
    });
    
    input.addEventListener('blur', () => {
        if (input.value.trim()) {
            addTag(input.value.trim());
        }
    });
}

// Handle file selection
document.getElementById('documents').addEventListener('change', (e) => {
    const fileList = Array.from(e.target.files).map(f => f.name).join(', ');
    document.getElementById('selectedFiles').textContent = fileList || 'No files selected';
});

// Initialize tag inputs
setupTagInput('sourceUrlsInput', 'sourceUrls');
setupTagInput('queryDomainsInput', 'queryDomains');

// Research form submission
async function startResearch(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const spinner = submitBtn.querySelector('.spinner');
    const submitText = submitBtn.querySelector('span');
    const progress = document.getElementById('progress');
    const output = document.getElementById('output');
    const error = document.getElementById('error');
    
    // Reset UI
    error.style.display = 'none';
    output.style.display = 'none';
    output.textContent = '';
    submitBtn.disabled = true;
    spinner.style.display = 'block';
    submitText.textContent = 'Researching...';
    progress.style.display = 'block';
    
    try {
        const formData = new FormData(form);
        
        // Handle file uploads
        const fileInput = form.querySelector('#documents');
        const files = fileInput.files;
        if (files.length > 0) {
            // Remove any existing file entries
            formData.delete('documents');
            // Add each file to formData
            for (let i = 0; i < files.length; i++) {
                formData.append('documents', files[i]);
            }
        }
        
        const queryParams = new URLSearchParams();
        // Add non-file parameters to queryParams
        for (const [key, value] of formData.entries()) {
            if (key !== 'documents') {
                queryParams.append(key, value);
            }
        }
        
        // Create the request URL with query parameters
        const url = `/research?${queryParams.toString()}`;
        
        // Send the request with files
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Research failed: ${response.statusText}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        output.style.display = 'block';
        
        let buffer = '';
        
        while (true) {
            const {value, done} = await reader.read();
            if (done) break;
            
            const text = decoder.decode(value, {stream: true});
            buffer += text;
            
            // Check for data events
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep the last incomplete line in the buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'report_complete') {
                            // Hide the progress indicator when report is complete
                            progress.style.display = 'none';
                            
                            // Reset submit button
                            submitBtn.disabled = false;
                            spinner.style.display = 'none';
                            submitText.textContent = 'Start Research';
                            
                            // Show the report container
                            const reportContainer = document.getElementById('report-container');
                            const reportContent = document.getElementById('report-content');
                            const reportDownloads = document.getElementById('report-downloads');
                            
                            reportContainer.style.display = 'block';
                            
                            // Set the report content with markdown formatting
                            reportContent.innerHTML = marked.parse(data.content);
                            
                            // Clear previous download buttons
                            reportDownloads.innerHTML = '';
                            
                            // Create filename base from query
                            const filenameBase = data.query ? 
                                data.query.substring(0, 30).replace(/[^a-z0-9]/gi, '_') : 
                                'research_report';
                            
                            // Add download buttons
                            const buttonContainer = document.createElement('div');
                            buttonContainer.className = 'download-buttons';
                            
                            // Add download buttons for each file type
                            const fileTypes = {
                                'md': 'Markdown',
                                'pdf': 'PDF',
                                'docx': 'DOCX',
                                'json': 'JSON Log'
                            };
                            
                            for (const [type, label] of Object.entries(fileTypes)) {
                                if (data.files[type]) {
                                    const btn = document.createElement('a');
                                    btn.className = 'download-button';
                                    btn.id = `download-${type}`;
                                    btn.href = data.files[type];
                                    btn.target = '_blank';
                                    
                                    // Check if file is ready
                                    if (window.readyFiles && window.readyFiles.includes(type)) {
                                        btn.innerHTML = `<span class="download-icon">⬇️</span> ${label}`;
                                    } else {
                                        btn.innerHTML = `<span class="download-icon">⏳</span> ${label} (Generating...)`;
                                        btn.classList.add('generating');
                                        btn.onclick = function(e) {
                                            if (this.classList.contains('generating')) {
                                                e.preventDefault();
                                                alert('File is still being generated. Please wait.');
                                                return false;
                                            }
                                        };
                                    }
                                    buttonContainer.appendChild(btn);
                                }
                            }
                            
                            reportDownloads.appendChild(buttonContainer);
                            
                            // Scroll to the report
                            reportContainer.scrollIntoView({behavior: 'smooth'});
                        } else if (data.type === 'research_complete') {
                            // Hide the progress indicator when research is complete
                            progress.style.display = 'none';
                            
                            // Reset submit button
                            submitBtn.disabled = false;
                            spinner.style.display = 'none';
                            submitText.textContent = 'Start Research';
                            
                            // Add a message to the output
                            output.textContent += `\n${data.message}\n`;
                            output.scrollTop = output.scrollHeight;
                            
                            // Initialize ready files tracking
                            window.readyFiles = [];
                        } else if (data.type === 'file_generation_started') {
                            // Add a message to the output
                            output.textContent += `\n${data.message}\n`;
                            output.scrollTop = output.scrollHeight;
                        } else if (data.type === 'file_ready') {
                            // Track which files are ready
                            if (!window.readyFiles) window.readyFiles = [];
                            window.readyFiles.push(data.format);
                            
                            // Update button if it exists
                            const btn = document.getElementById(`download-${data.format}`);
                            if (btn) {
                                btn.innerHTML = `<span class="download-icon">⬇️</span> ${fileTypes[data.format]}`;
                                btn.classList.remove('generating');
                                btn.onclick = null; // Remove click handler
                            }
                            
                            // Add a message to the output
                            output.textContent += `\n${data.format.toUpperCase()} file is ready for download\n`;
                            output.scrollTop = output.scrollHeight;
                        } else if (data.type === 'files_ready') {
                            // Add a message to the output
                            output.textContent += `\n${data.message}\n`;
                            output.scrollTop = output.scrollHeight;
                            
                            // Update all buttons
                            for (const format in data.files) {
                                const btn = document.getElementById(`download-${format}`);
                                if (btn) {
                                    btn.innerHTML = `<span class="download-icon">⬇️</span> ${fileTypes[format] || format.toUpperCase()}`;
                                    btn.classList.remove('generating');
                                    btn.onclick = null; // Remove click handler
                                }
                            }
                        }
                    } catch (e) {
                        console.error('Failed to parse data event:', e);
                    }
                } else {
                    // Update the output with regular log lines
                    output.textContent += line + '\n';
                    output.scrollTop = output.scrollHeight;
                }
            }
        }
    } catch (err) {
        error.textContent = err.message;
        error.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        submitText.textContent = 'Start Research';
        progress.style.display = 'none';
    }
}

// Function to download content as a file
function downloadAsFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Function to generate and download PDF
function generateAndDownloadPDF(markdownContent, filename) {
    // Convert markdown to HTML
    const htmlContent = marked.parse(markdownContent);
    
    // Alert user that we're using client-side PDF generation
    alert('PDF generation is being handled in the browser. For production use, consider using a server-side PDF generation service for better formatting.');
    
    // Use html2pdf.js or similar library if available
    if (window.html2pdf) {
        const element = document.createElement('div');
        element.className = 'pdf-container';
        element.innerHTML = htmlContent;
        document.body.appendChild(element);
        
        const opt = {
            margin: [10, 10],
            filename: filename,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };
        
        html2pdf().set(opt).from(element).save().then(() => {
            document.body.removeChild(element);
        });
    } else {
        // Fallback to simple download as HTML if html2pdf is not available
        downloadAsFile(htmlContent, filename.replace('.pdf', '.html'), 'text/html');
        alert('PDF generation library not available. Downloaded as HTML instead.');
    }
}

// Function to generate and download DOCX
function generateAndDownloadDOCX(markdownContent, filename) {
    // Alert user that we're using client-side DOCX generation
    alert('DOCX generation is being handled in the browser. For production use, consider using a server-side DOCX generation service for better formatting.');
    
    // Use docx.js or similar library if available
    if (window.docx) {
        // Implementation would go here if docx.js is available
        // This is a placeholder for actual implementation
        alert('DOCX generation not fully implemented in this version.');
        downloadAsFile(markdownContent, filename.replace('.docx', '.md'), 'text/markdown');
    } else {
        // Fallback to simple download as markdown
        downloadAsFile(markdownContent, filename.replace('.docx', '.md'), 'text/markdown');
        alert('DOCX generation library not available. Downloaded as Markdown instead.');
    }
}

// Add event listener for file input changes
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('documents');
    const selectedFiles = document.getElementById('selectedFiles');
    
    fileInput.addEventListener('change', function() {
        selectedFiles.innerHTML = '';
        if (this.files.length > 0) {
            const fileList = document.createElement('ul');
            fileList.className = 'file-list';
            
            Array.from(this.files).forEach(file => {
                const li = document.createElement('li');
                li.textContent = file.name;
                fileList.appendChild(li);
            });
            
            selectedFiles.appendChild(fileList);
        }
    });
}); 