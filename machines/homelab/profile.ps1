#!/usr/bin/env pwsh

function Wake-PC {
    # Realtek PCIe 2.5GbE Family Controller
    Write-Host "Waking up PC (Ethernet)..."
    wakeonlan BC-FC-E7-D6-D0-9D

    # MediaTek Wi-Fi 6E MT7922 (RZ616)
    Write-Host "Waking up PC (WiFi)..."
    wakeonlan D8-B3-2F-69-8D-09
}
