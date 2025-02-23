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
        const queryParams = new URLSearchParams(formData);
        
        const response = await fetch(`/research?${queryParams.toString()}`);
        
        if (!response.ok) {
            throw new Error(`Research failed: ${response.statusText}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        output.style.display = 'block';
        
        while (true) {
            const {value, done} = await reader.read();
            if (done) break;
            
            const text = decoder.decode(value, {stream: true});
            output.textContent += text;
            output.scrollTop = output.scrollHeight;
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