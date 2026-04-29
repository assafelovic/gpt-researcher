import React, { useState, useEffect } from 'react';

interface MCPConfig {
  name: string;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  connection_url?: string;
  connection_type?: string;
  connection_headers?: Record<string, string>;
  preset?: string;
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
  const [configText, setConfigText] = useState(() => {
    // Initialize with the passed configs, handling empty array case
    if (Array.isArray(mcpConfigs) && mcpConfigs.length > 0) {
      return JSON.stringify(mcpConfigs, null, 2);
    }
    return '[]';
  });
  const [validationStatus, setValidationStatus] = useState<{
    isValid: boolean;
    message: string;
    serverCount?: number;
  }>({ isValid: true, message: 'Valid JSON ✓' });
  const [showInfoModal, setShowInfoModal] = useState(false);

  useEffect(() => {
    validateConfig(configText);
  }, [configText]);

  // Sync with props when they change (for localStorage loading)
  useEffect(() => {
    setEnabled(mcpEnabled);
  }, [mcpEnabled]);

  useEffect(() => {
    if (Array.isArray(mcpConfigs)) {
      const newConfigText = mcpConfigs.length > 0 ? JSON.stringify(mcpConfigs, null, 2) : '[]';
      setConfigText(newConfigText);
    }
  }, [mcpConfigs]);

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
        if (!server.command && !server.connection_url && !server.preset) {
          errors.push(`Server ${index + 1}: missing command, connection_url, or preset`);
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

  // Helper function to check if a preset is currently selected
  const isPresetSelected = (presetName: string): boolean => {
    try {
      const currentText = configText.trim();
      if (!currentText || currentText === '[]') return false;
      
      const parsed = JSON.parse(currentText);
      if (!Array.isArray(parsed)) return false;
      
      return parsed.some(server => server.name === presetName);
    } catch {
      return false;
    }
  };

  const togglePreset = (preset: string) => {
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
      },
      katailyst: {
        name: 'katailyst',
        preset: 'katailyst'
      },
      metabase: {
        name: 'metabase',
        preset: 'metabase'
      }
    };

    const config = presets[preset];
    if (!config) {
      return;
    }

    try {
      let currentConfig: MCPConfig[] = [];
      const currentText = configText.trim();

      if (currentText && currentText !== '[]') {
        currentConfig = JSON.parse(currentText);
      }

      const existingIndex = currentConfig.findIndex(server => server.name === config.name);

      if (existingIndex !== -1) {
        // Remove the preset if it exists (deselect)
        currentConfig.splice(existingIndex, 1);
      } else {
        // Add the preset if it doesn't exist (select)
        currentConfig.push(config);
      }

      const newText = JSON.stringify(currentConfig, null, 2);
      
      setConfigText(newText);
      
      // IMPORTANT: Also call onMCPChange immediately with the new config
      if (enabled) {
        onMCPChange(enabled, currentConfig);
      }
      
    } catch (error) {
      console.error('Error toggling MCP preset:', error);
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
            aria-label="Learn about MCP"
          >
            <svg
              aria-hidden="true"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              width="16"
              height="16"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
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
                  className={`settings preset-btn ${isPresetSelected('github') ? 'selected' : ''}`}
                  onClick={() => togglePreset('github')}
                >
                  <i className="fab fa-github"></i> GitHub
                </button>
                <button
                  type="button"
                  className={`settings preset-btn ${isPresetSelected('tavily') ? 'selected' : ''}`}
                  onClick={() => togglePreset('tavily')}
                >
                  <i className="fas fa-search"></i> Tavily Web Search
                </button>
                <button
                  type="button"
                  className={`settings preset-btn ${isPresetSelected('filesystem') ? 'selected' : ''}`}
                  onClick={() => togglePreset('filesystem')}
                >
                  <i className="fas fa-folder"></i> Local Files
                </button>
                <button
                  type="button"
                  className={`settings preset-btn ${isPresetSelected('katailyst') ? 'selected' : ''}`}
                  onClick={() => togglePreset('katailyst')}
                >
                  <i className="fas fa-network-wired"></i> Katailyst
                </button>
                <button
                  type="button"
                  className={`settings preset-btn ${isPresetSelected('metabase') ? 'selected' : ''}`}
                  onClick={() => togglePreset('metabase')}
                >
                  <i className="fas fa-chart-line"></i> Metrics
                </button>
              </div>
              <small className="text-muted" style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.85rem', marginTop: '8px', display: 'block' }}>
                HLT presets expand server-side from Railway env, so private tokens never enter the browser.
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
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>args</code>,{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>connection_url</code>, and optional{' '}
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
                <li><span className="highlight">connection_url:</span> Hosted MCP endpoint URL for HTTP or WebSocket servers</li>
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
