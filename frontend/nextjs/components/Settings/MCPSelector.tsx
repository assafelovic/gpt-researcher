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
  }>({ isValid: true, message: 'Gültiges JSON ✓' });
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
      setValidationStatus({ isValid: true, message: 'Leere Konfiguration' });
      return true;
    }

    try {
      const parsed = JSON.parse(text);

      if (!Array.isArray(parsed)) {
        throw new Error('Die Konfiguration muss ein Array sein');
      }

      const errors: string[] = [];
      parsed.forEach((server: any, index: number) => {
        if (!server.name) {
          errors.push(`Server ${index + 1}: Name fehlt`);
        }
        if (!server.command && !server.connection_url) {
          errors.push(`Server ${index + 1}: command oder connection_url fehlt`);
        }
      });

      if (errors.length > 0) {
        throw new Error(errors.join('; '));
      }

      setValidationStatus({
        isValid: true,
        message: `Gültiges JSON ✓ (${parsed.length} Server${parsed.length !== 1 ? 'e' : ''})`,
        serverCount: parsed.length
      });
      return true;
    } catch (error: any) {
      setValidationStatus({
        isValid: false,
        message: `Ungültiges JSON: ${error.message}`
      });
      return false;
    }
  };

  const handleEnabledChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnabled = e.target.checked;
    console.log('🔍 DEBUG: MCP enabled changed to:', newEnabled);
    setEnabled(newEnabled);

    if (newEnabled && validationStatus.isValid) {
      try {
        const configs = JSON.parse(configText || '[]');
        console.log('🔍 DEBUG: Calling onMCPChange with configs:', configs);
        onMCPChange(newEnabled, configs);
      } catch {
        console.log('🔍 DEBUG: JSON parse failed, calling with empty array');
        onMCPChange(newEnabled, []);
      }
    } else {
      console.log('🔍 DEBUG: Disabled or invalid, calling with empty array');
      onMCPChange(newEnabled, []);
    }
  };

  const handleConfigChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    console.log('🔍 DEBUG: Config text changed to:', newText);
    setConfigText(newText);

    if (enabled && validateConfig(newText)) {
      try {
        const configs = JSON.parse(newText || '[]');
        console.log('🔍 DEBUG: Parsed configs from textarea:', configs);
        console.log('🔍 DEBUG: Calling onMCPChange from textarea with:', { enabled, configs });
        onMCPChange(enabled, configs);
      } catch {
        console.log('🔍 DEBUG: JSON parse failed in textarea change');
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
    console.log('🔍 DEBUG: togglePreset called with:', preset);
    console.log('🔍 DEBUG: Current configText:', configText);
    console.log('🔍 DEBUG: MCP enabled:', enabled);

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
    if (!config) {
      console.log('🔍 DEBUG: Preset config not found for:', preset);
      return;
    }

    try {
      let currentConfig: MCPConfig[] = [];
      const currentText = configText.trim();

      if (currentText && currentText !== '[]') {
        currentConfig = JSON.parse(currentText);
      }
      console.log('🔍 DEBUG: Current parsed config:', currentConfig);

      const existingIndex = currentConfig.findIndex(server => server.name === config.name);
      console.log('🔍 DEBUG: Existing index for', config.name, ':', existingIndex);

      if (existingIndex !== -1) {
        // Remove the preset if it exists (deselect)
        console.log('🔍 DEBUG: Removing preset');
        currentConfig.splice(existingIndex, 1);
      } else {
        // Add the preset if it doesn't exist (select)
        console.log('🔍 DEBUG: Adding preset');
        currentConfig.push(config);
      }

      const newText = JSON.stringify(currentConfig, null, 2);
      console.log('🔍 DEBUG: New config text:', newText);
      console.log('🔍 DEBUG: Final config array:', currentConfig);

      setConfigText(newText);

      // IMPORTANT: Also call onMCPChange immediately with the new config
      if (enabled) {
        console.log('🔍 DEBUG: Calling onMCPChange from togglePreset with:', { enabled, currentConfig });
        onMCPChange(enabled, currentConfig);
      }

    } catch (error) {
      console.error('🔍 DEBUG: Error toggling preset:', error);
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
            MCP aktivieren (Model Context Protocol)
          </label>
          <button
            type="button"
            className="settings mcp-info-btn"
            onClick={() => setShowInfoModal(true)}
          title="Mehr über MCP erfahren"
          >
            ℹ️
          </button>
        </div>
        <small className="text-muted" style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.85rem', marginBottom: '15px', display: 'block' }}>
          Verbinde dich über MCP-Server mit externen Werkzeugen und Datenquellen
        </small>

        {enabled && (
          <div className="settings mcp-config-section">
            <div className="settings mcp-presets">
              <label className="agent_question" style={{ marginBottom: '10px' }}>Schnellvorlagen</label>
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
                  <i className="fas fa-search"></i> Tavily-Websuche
                </button>
                <button
                  type="button"
                  className={`settings preset-btn ${isPresetSelected('filesystem') ? 'selected' : ''}`}
                  onClick={() => togglePreset('filesystem')}
                >
                  <i className="fas fa-folder"></i> Lokale Dateien
                </button>
              </div>
              <small className="text-muted" style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.85rem', marginTop: '8px', display: 'block' }}>
                Klicke auf eine Vorlage, um MCP-Server in der Konfiguration unten umzuschalten. Ausgewählte Vorlagen werden hervorgehoben.
              </small>
            </div>

            <div className="settings mcp-config-group">
              <label className="agent_question" style={{ marginBottom: '10px' }}>MCP-Server-Konfiguration</label>
              <textarea
                className={`settings mcp-config-textarea ${validationStatus.isValid ? 'valid' : 'invalid'}`}
                rows={12}
                placeholder="Füge deine MCP-Server-Konfiguration als JSON-Array ein ..."
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
                  <i className="fas fa-code"></i> JSON formatieren
                </button>
              </div>
              <small className="text-muted" style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.85rem', marginTop: '8px', display: 'block', lineHeight: '1.4' }}>
                Füge deine MCP-Server-Konfiguration als JSON-Array ein. Jeder Server sollte Eigenschaften wie{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>name</code>,{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>command</code>,{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>args</code>, und optional{' '}
                <code style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', padding: '2px 4px', borderRadius: '3px', color: '#0d9488' }}>env</code> variables.{' '}
                <a
                  href="#"
                  className="settings mcp-example-link"
                  onClick={(e) => { e.preventDefault(); showExample(); }}
                  style={{ color: '#0d9488', textDecoration: 'none', fontWeight: '500' }}
                >
                  Beispiel anzeigen →
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
              <p>MCP ermöglicht es GPT Researcher, über ein standardisiertes Protokoll mit externen Werkzeugen und Datenquellen zu kommunizieren.</p>

              <h4 className="highlight">Vorteile:</h4>
              <ul>
                <li><span className="highlight">Lokale Daten nutzen:</span> Verbinde Datenbanken, Dateisysteme und APIs</li>
                <li><span className="highlight">Externe Werkzeuge verwenden:</span> Integriere Webdienste und Tools von Drittanbietern</li>
                <li><span className="highlight">Funktionen erweitern:</span> Füge über MCP-Server eigene Funktionalität hinzu</li>
                <li><span className="highlight">Sicherheit bewahren:</span> Kontrollierter Zugriff mit sauberer Authentifizierung</li>
              </ul>

              <h4 className="highlight">Schnellstart:</h4>
              <ul>
                <li>Aktiviere MCP über das Kontrollkästchen oben</li>
                <li>Klicke auf eine Vorlage, um vorkonfigurierte Server zum JSON hinzuzufügen</li>
                <li>Oder füge deine eigene MCP-Konfiguration als JSON-Array ein</li>
                <li>Starte deine Recherche - MCP läuft dann mit optimalen Einstellungen</li>
              </ul>

              <h4 className="highlight">Konfigurationsformat:</h4>
              <p>Jeder MCP-Server sollte ein JSON-Objekt mit diesen Eigenschaften sein:</p>
              <ul>
                <li><span className="highlight">name:</span> Eindeutiger Bezeichner (z. B. &quot;github&quot;, &quot;filesystem&quot;)</li>
                <li><span className="highlight">command:</span> Befehl zum Starten des Servers (z. B. &quot;npx&quot;, &quot;python&quot;)</li>
                <li><span className="highlight">args:</span> Argumente-Array (z. B. [&quot;-y&quot;, &quot;@modelcontextprotocol/server-github&quot;])</li>
                <li><span className="highlight">env:</span> Objekt mit Umgebungsvariablen (z. B. {JSON.stringify({API_KEY: "dein_schluessel"})})</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MCPSelector;
