$ErrorActionPreference = "Stop"

$imagesDir = "docs/images"
if (!(Test-Path $imagesDir)) {
    New-Item -ItemType Directory -Path $imagesDir -Force | Out-Null
}

$routes = @(
    @{ name = "01_landing_hero.png"; url = "https://procurax-five.vercel.app/#/" },
    @{ name = "02_control_tower.png"; url = "https://procurax-five.vercel.app/#/workspace/control-tower" },
    @{ name = "03_impact_network.png"; url = "https://procurax-five.vercel.app/#/workspace/impact-map" },
    @{ name = "04_scenario_studio.png"; url = "https://procurax-five.vercel.app/#/workspace/scenario-studio" },
    @{ name = "05_evidence_copilot.png"; url = "https://procurax-five.vercel.app/#/workspace/evidence-panel" },
    @{ name = "06_executive_approvals.png"; url = "https://procurax-five.vercel.app/#/workspace/approvals" },
    @{ name = "07_evaluation_benchmarks.png"; url = "https://procurax-five.vercel.app/#/workspace/evaluation" },
    @{ name = "08_data_sources.png"; url = "https://procurax-five.vercel.app/#/workspace/data-sources" }
)

foreach ($r in $routes) {
    $outPath = Join-Path $imagesDir $r.name
    Write-Host "Capturing $($r.name) from $($r.url)..."
    npx playwright screenshot --channel chrome --viewport-size="1440,900" --wait-for-timeout=4000 $r.url $outPath
}

Write-Host "All screenshots captured successfully!"
