import sys

def run():
    replacements = {
        'frontend/src/workspace.css': [
            ('color: #172033;', 'color: #1D2926;'),
            ('--border-cyan: #29B6E6;', '--border-copper: #E58B45;\n  --border-cyan: #E58B45;'),
            ('--text-main: #172033;', '--text-main: #1D2926;'),
            ('--text-muted: #5D6B82;', '--text-muted: #64716B;'),
            ('--sapphire-primary: #3558E8;', '--forest-primary: #176B55;\n  --sapphire-primary: #176B55;'),
            ('--sapphire-hover: #2647D0;', '--forest-hover: #105642;\n  --sapphire-hover: #105642;'),
            ('--cyan-accent: #29B6E6;', '--copper-accent: #E58B45;\n  --sage-accent: #BDE3D2;\n  --cyan-accent: #E58B45;'),
            ('--cyan-bright: #29B6E6;', '--cyan-bright: #E58B45;'),
            ('--cyan-primary: #3558E8;', '--cyan-primary: #176B55;'),
            ('--blue-primary: #3558E8;', '--blue-primary: #176B55;'),
            ('--indigo-primary: #4F6AF0;', '--indigo-primary: #176B55;'),
            ('.metric-icon.blue { background: rgba(23, 107, 85, 0.1); color: var(--sapphire-primary); }', '.metric-icon.blue { background: rgba(23, 107, 85, 0.1); color: var(--forest-primary); }'),
            ('.metric-icon.teal { background: rgba(229, 139, 69, 0.12); color: #0E80A8; }', '.metric-icon.teal { background: rgba(189, 227, 210, 0.35); color: #176B55; }'),
        ],
        'frontend/src/Workspace.tsx': [
            ("color: '#3558E8' },", "color: '#176B55' },"),
            ("color: '#29B6E6' },", "color: '#536F83' },"),
            ("color: 'var(--sapphire-primary, #3558E8)'", "color: 'var(--forest-primary, #176B55)'"),
        ],
        'frontend/src/App.tsx': [
            ('stopColor="#3558E8"', 'stopColor="#176B55"'),
            ('stroke="#3558E8"', 'stroke="#176B55"'),
            ('fill="#29B6E6"', 'fill="#E58B45"'),
        ],
        'frontend/src/components/ControlTowerView.tsx': [
            ("background: signalFilter === cat ? '#3558E8' : '#ffffff'", "background: signalFilter === cat ? '#176B55' : '#ffffff'"),
            ("color: signalFilter === cat ? '#fff' : '#5D6B82'", "color: signalFilter === cat ? '#fff' : '#64716B'"),
        ],
        'frontend/src/components/ScenarioStudioView.tsx': [
            ("border: isActive ? '1px solid #3558E8' : '1px solid #E7E5DC'", "border: isActive ? '1px solid #E58B45' : '1px solid #E7E5DC'"),
            ("color: isActive ? '#3558E8' : 'var(--text-main)'", "color: isActive ? '#E58B45' : 'var(--text-main)'"),
            ("color: '#5D6B82'", "color: '#64716B'"),
            ("color: '#29B6E6'", "color: '#176B55'"),
            ("color: '#3558E8'", "color: '#176B55'"),
            ("background: isActive ? 'rgba(23, 107, 85, 0.08)'", "background: isActive ? 'rgba(229, 139, 69, 0.08)'"),
            ("boxShadow: isActive ? '0 2px 12px rgba(23, 107, 85, 0.15)'", "boxShadow: isActive ? '0 2px 12px rgba(229, 139, 69, 0.15)'"),
        ],
        'frontend/src/components/ImpactMapView.tsx': [
            ("color: activeTab === 'NETWORK' ? '#fff' : '#5D6B82'", "color: activeTab === 'NETWORK' ? '#fff' : '#64716B'"),
            ("color: activeTab === 'WAREHOUSE' ? '#fff' : '#5D6B82'", "color: activeTab === 'WAREHOUSE' ? '#fff' : '#64716B'"),
            ("color: '#5D6B82'", "color: '#64716B'"),
            ("color: '#3558E8'", "color: '#176B55'"),
        ],
        'frontend/src/components/EvaluationDashboardView.tsx': [
            ("color: '#3558E8'", "color: '#176B55'"),
            ("color: '#5D6B82'", "color: '#64716B'"),
            ("borderColor: activeTab === 'leaderboard' ? '#3558E8' : 'transparent'", "borderColor: activeTab === 'leaderboard' ? '#176B55' : 'transparent'"),
            ("borderColor: activeTab === 'forecasting' ? '#3558E8' : 'transparent'", "borderColor: activeTab === 'forecasting' ? '#176B55' : 'transparent'"),
            ("borderColor: activeTab === 'sentiment' ? '#3558E8' : 'transparent'", "borderColor: activeTab === 'sentiment' ? '#176B55' : 'transparent'"),
            ("borderColor: activeTab === 'pareto' ? '#3558E8' : 'transparent'", "borderColor: activeTab === 'pareto' ? '#176B55' : 'transparent'"),
            ("borderColor: activeTab === 'audit' ? '#3558E8' : 'transparent'", "borderColor: activeTab === 'audit' ? '#176B55' : 'transparent'"),
        ],
        'frontend/src/components/DataSourcesView.tsx': [
            ("color: '#3558E8'", "color: '#176B55'"),
            ("color: '#5D6B82'", "color: '#64716B'"),
            ("color: '#172033'", "color: '#1D2926'"),
        ],
        'frontend/src/components/IntegrationSettingsView.tsx': [
            ("color: '#5D6B82'", "color: '#64716B'"),
        ]
    }

    for fp, repl_list in replacements.items():
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
        orig = content
        for old, new in repl_list:
            content = content.replace(old, new)
        if content != orig:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Successfully updated {fp}')
        else:
            print(f'No changes needed in {fp}')

if __name__ == '__main__':
    run()
