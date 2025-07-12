import React, { useState, useEffect } from 'react';

interface MCPConfig {
  name: string;
  command: string;
  args: string[];
  env: Record<string, string>;
}

interface MCPSelectorProps {
  mcpEnabled: boolean;
  mcpConfigs: MCPConfig[];
  onMCPChange: (enabled: boolean, configs: MCPConfig[]) => void;
}

const MCPSelector: React.FC<MCPSelectorProps> = ({
  mcpEnabled,
  mcpConfigs,
  onMCPChange,
}) => {
  const [enabled, setEnabled] = useState(mcpEnabled);
  const [configText, setConfigText] = useState(
    JSON.stringify(mcpConfigs, null, 2)
  );
  const [validationStatus, setValidationStatus] = useState<{
    isValid: boolean;
    message: string;
    serverCount?: number;
  }>({ isValid: true, message: 'Valid JSON ✓' });
  const [showInfoModal, setShowInfoModal] = useState(false);

  useEffect(() => {
    validateConfig(configText);
  }, [configText]);

  const validateConfig = (text: string) => {
    if (!text.trim() || text.trim() === '[]') {
      setValidationStatus({ isValid: true, message: 'Empty configuration' });
      return true;
    }

    try {
      const parsed = JSON.parse(text);
      
      if (!Array.isArray(parsed)) {
        throw new Error('Configuration must be an array');
      }

      const errors: string[] = [];
      parsed.forEach((server: any, index: number) => {
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

      setValidationStatus({
        isValid: true,
        message: `Valid JSON ✓ (${parsed.length} server${parsed.length !== 1 ? 's' : ''})`,
        serverCount: parsed.length
      });
      return true;
    } catch (error: any) {
      setValidationStatus({
        isValid: false,
        message: `Invalid JSON: ${error.message}`
      });
      return false;
    }
  };

  const handleEnabledChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnabled = e.target.checked;
    setEnabled(newEnabled);
    
    if (newEnabled && validationStatus.isValid) {
      try {
        const configs = JSON.parse(configText || '[]');
        onMCPChange(newEnabled, configs);
      } catch {
        onMCPChange(newEnabled, []);
      }
    } else {
      onMCPChange(newEnabled, []);
    }
  };

  const handleConfigChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setConfigText(newText);
    
    if (enabled && validateConfig(newText)) {
      try {
        const configs = JSON.parse(newText || '[]');
        onMCPChange(enabled, configs);
      } catch {
        // Invalid JSON, don't update
      }
    }
  };

  const formatJSON = () => {
    try {
      const parsed = JSON.parse(configText || '[]');
      const formatted = JSON.stringify(parsed, null, 2);
      setConfigText(formatted);
    } catch {
      // Invalid JSON, don't format
    }
  };

  const addPreset = (preset: string) => {
    const presets: Record<string, MCPConfig> = {
      github: {
        name: 'github',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-github'],
        env: {
          GITHUB_PERSONAL_ACCESS_TOKEN: 'your_github_token_here'
        }
      },
      tavily: {
        name: 'tavily',
        command: 'npx',
        args: ['-y', 'tavily-mcp@0.1.2'],
        env: {
          TAVILY_API_KEY: 'your_tavily_api_key_here'
        }
      },
      filesystem: {
        name: 'filesystem',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/allowed/directory'],
        env: {}
      }
    };

    const config = presets[preset];
    if (!config) return;

    try {
      let currentConfig: MCPConfig[] = [];
      const currentText = configText.trim();
      
      if (currentText && currentText !== '[]') {
        currentConfig = JSON.parse(currentText);
      }

      const existingIndex = currentConfig.findIndex(server => server.name === config.name);
      
      if (existingIndex !== -1) {
        currentConfig[existingIndex] = config;
      } else {
        currentConfig.push(config);
      }

      const newText = JSON.stringify(currentConfig, null, 2);
      setConfigText(newText);
    } catch (error) {
      console.error('Error adding preset:', error);
    }
  };

  const showExample = () => {
    const exampleConfig = [
      {
        name: 'github',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-github'],
        env: {
          GITHUB_PERSONAL_ACCESS_TOKEN: 'your_github_token_here'
        }
      },
      {
        name: 'filesystem',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/allowed/directory'],
        env: {}
      }
    ];

    setConfigText(JSON.stringify(exampleConfig, null, 2));
  };

  return (
    <div className="form-group">
      <div className="settings mcp-section">
        <div className="settings mcp-header">
          <label className="agent_question">
            <input
              type="checkbox"
              className="settings mcp-toggle"
              checked={enabled}
              onChange={handleEnabledChange}
            />
            Enable MCP (Model Context Protocol)
          </label>
          <button
            type="button"
            className="settings mcp-info-btn"
            onClick={() => setShowInfoModal(true)}
            title="Learn about MCP"
          >
            ℹ️
          </button>
        </div>
        <small className="text-muted" style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.85rem', marginBottom: '15px', display: 'block' }}>
          Connect to external tools and data sources through MCP servers
        </small>
        
        {enabled && (
          <div className="settings mcp-config-section">
            <div className="settings mcp-presets">
              <label className="agent_question" style={{ marginBottom: '10px' }}>Quick Presets</label>
              <div className="settings preset-buttons">
                <button
                  type="button"
                  className="settings preset-btn"
                  onClick={() => addPreset('github')}
                >
                  <i className="fab fa-github"></i> GitHub
                </button>
                <button
                  type="button"
                  className="settings preset-btn"
                  onClick={() => addPreset('tavily')}
                >
                  <i className="fas fa-search"></i> Tavily Web Search
                </button>
                <button
                  type="button"
                  className="settings preset-btn"
                  onClick={() => addPreset('filesystem')}
                >
                  <i className="fas fa-folder"></i> Local Files
                </button>
              </div>
              <small className="text-muted" style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.85rem', marginTop: '8px', display: 'block' }}>
                Click a preset to add pre-configured MCP servers to the JSON below
              </small>
            </div>

            <div className="settings mcp-config-group">
              <label className="agent_question" style={{ marginBottom: '10px' }}>MCP Servers Configuration</label>
              <textarea
                className={`settings mcp-config-textarea ${validationStatus.isValid ? 'valid' : 'invalid'}`}
                rows={12}
                placeholder="Paste your MCP servers configuration as JSON array..."
                value={configText}
                onChange={handleConfigChange}
                style={{ minHeight: '300px' }}
              />
              <div className="settings mcp-config-status">
                <span className={`settings mcp-status-text ${validationStatus.isValid ? 'valid' : 'invalid'}`}>
                  {validationStatus.message}
                </span>
                <button
                  type="button"
                  className="settings mcp-format-btn"
                  onClick={formatJSON}
                >
                  <i className="fas fa-code"></i> Format JSON
                </button>
              </div>
              <small className="text-muted" style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.85rem', marginTop: '8px', display: 'block', lineHeight: '1.4' }}>
                Paste your MCP servers configuration as a JSON array. Each server should have properties like{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>name</code>,{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>command</code>,{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>args</code>, and optional{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>env</code> variables.{' '}
                <a
                  href="#"
                  className="settings mcp-example-link"
                  onClick={(e) => { e.preventDefault(); showExample(); }}
                  style={{ color: '#0d9488', textDecoration: 'none', fontWeight: '500' }}
                >
                  See example →
                </a>
              </small>
            </div>
          </div>
        )}

        {/* MCP Info Modal */}
        {showInfoModal && (
          <div className="settings mcp-info-modal visible">
            <div className="settings mcp-info-content">
              <button
                className="settings mcp-info-close"
                onClick={() => setShowInfoModal(false)}
              >
                <i className="fas fa-times"></i>
              </button>
              <h3>Model Context Protocol (MCP)</h3>
              <p>MCP enables GPT Researcher to connect with external tools and data sources through a standardized protocol.</p>
              
              <h4 className="highlight">Benefits:</h4>
              <ul>
                <li><span className="highlight">Access Local Data:</span> Connect to databases, file systems, and APIs</li>
                <li><span className="highlight">Use External Tools:</span> Integrate with web services and third-party tools</li>
                <li><span className="highlight">Extend Capabilities:</span> Add custom functionality through MCP servers</li>
                <li><span className="highlight">Maintain Security:</span> Controlled access with proper authentication</li>
              </ul>

              <h4 className="highlight">Quick Start:</h4>
              <ul>
                <li>Enable MCP using the checkbox above</li>
                <li>Click a preset to add pre-configured servers to the JSON</li>
                <li>Or paste your own MCP configuration as a JSON array</li>
                <li>Start your research - MCP will run with optimal settings</li>
              </ul>

              <h4 className="highlight">Configuration Format:</h4>
              <p>Each MCP server should be a JSON object with these properties:</p>
              <ul>
                <li><span className="highlight">name:</span> Unique identifier (e.g., &quot;github&quot;, &quot;filesystem&quot;)</li>
                <li><span className="highlight">command:</span> Command to run the server (e.g., &quot;npx&quot;, &quot;python&quot;)</li>
                <li><span className="highlight">args:</span> Array of arguments (e.g., [&quot;-y&quot;, &quot;@modelcontextprotocol/server-github&quot;])</li>
                <li><span className="highlight">env:</span> Object with environment variables (e.g., {JSON.stringify({API_KEY: "your_key"})})</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MCPSelector; 