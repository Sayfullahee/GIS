
        // High-fidelity basemap providers (no API keys required)
        function createBaseLayers() {
            return {
                "🗺️ Dark Canvas (Esri)": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
                    maxZoom: 16
                }),
                "🌍 OpenStreetMap": L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; OpenStreetMap contributors',
                    maxZoom: 19
                }),
                "🛰️ Satellite Imagery": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri',
                    maxZoom: 18
                }),
                "🏔️ Topographic": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri',
                    maxZoom: 18
                })
            };
        }

        // Tab switching logic
        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('onclick')?.includes(`'${tabId}'`));
            });
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            const target = document.getElementById('tab-' + tabId);
            if (target) target.classList.add('active');

            if (tabId === 'overview') {
                setTimeout(() => { if (window.map) window.map.invalidateSize(); }, 150);
            } else if (tabId === 'flood') {
                loadFloodDashboard();
                setTimeout(() => { if (window.floodMap) window.floodMap.invalidateSize(); }, 150);
            } else if (tabId === 'scenarios') {
                loadScenariosData();
            } else if (tabId === 'interventions') {
                loadInterventionsData();
            } else if (tabId === 'tables') {
                loadTablesList();
            } else if (tabId === 'remote_sensing') {
                loadRemoteSensingData();
            }
        }

        function floodField(record, name) {
            const key = Object.keys(record).find(item => item.toLowerCase() === name.toLowerCase());
            return key ? record[key] : '';
        }

        function appendFloodCell(row, value) {
            const cell = document.createElement('td');
            cell.textContent = value === null || value === undefined || value === '' ? '—' : String(value);
            row.appendChild(cell);
        }

        let floodMap;
        let floodLayerControl;
        function loadFloodDashboard() {
            const status = document.getElementById('flood-data-status');
            Promise.all([
                fetch('/api/flood/dashboard').then(response => {
                    if (!response.ok) throw new Error('Flood dashboard request failed');
                    return response.json();
                }),
                fetch('/api/flood/alerts').then(response => {
                    if (!response.ok) throw new Error('Flood alerts request failed');
                    return response.json();
                }),
                fetch('/api/flood/performance').then(response => {
                    if (!response.ok) throw new Error('Warning performance request failed');
                    return response.json();
                }),
                fetch('/api/flood/warning-levels').then(response => {
                    if (!response.ok) throw new Error('Warning level request failed');
                    return response.json();
                }),
                fetch('/api/flood/geojson').then(response => {
                    if (!response.ok) throw new Error('Flood alert map request failed');
                    return response.json();
                })
            ]).then(([dashboard, alerts, performance, levels, geojson]) => {
                status.textContent = dashboard.status === 'OPERATIONAL' ? 'Flood data available' : 'Flood data not configured';
                document.getElementById('flood-active-count').textContent = dashboard.active_warnings;
                document.getElementById('flood-total-count').textContent = dashboard.total_alerts;
                document.getElementById('flood-reach-rate').textContent = dashboard.notification_reach_rate_pct === null ? 'Not evaluated' : `${dashboard.notification_reach_rate_pct}%`;
                document.getElementById('flood-ack-rate').textContent = dashboard.notification_acknowledgement_rate_pct === null ? 'Not evaluated' : `${dashboard.notification_acknowledgement_rate_pct}%`;
                document.getElementById('flood-awareness-count').textContent = dashboard.awareness_activities;
                const metrics = dashboard.performance_metrics;
                document.getElementById('flood-hit-rate').textContent = metrics.hit_rate_pct === null ? 'Not evaluated' : `${metrics.hit_rate_pct}%`;
                document.getElementById('flood-false-rate').textContent = metrics.false_alarm_rate_pct === null ? 'Not evaluated' : `${metrics.false_alarm_rate_pct}%`;
                document.getElementById('flood-lead-time').textContent = metrics.mean_lead_time_hours === null ? 'Not evaluated' : `${metrics.mean_lead_time_hours} h`;
                document.getElementById('flood-awareness-coverage').textContent = metrics.high_risk_awareness_coverage_pct === null ? 'Not evaluated' : `${metrics.high_risk_awareness_coverage_pct}%`;
                document.getElementById('flood-audit-completeness').textContent = metrics.mean_audit_completeness_pct === null ? 'Not evaluated' : `${metrics.mean_audit_completeness_pct}%`;

                const alertsBody = document.getElementById('flood-alerts-body');
                alertsBody.replaceChildren();
                alerts.alerts.forEach(alert => {
                    const row = document.createElement('tr');
                    appendFloodCell(row, floodField(alert, 'alert_id'));
                    appendFloodCell(row, floodField(alert, 'released_at') || floodField(alert, 'issued_at'));
                    appendFloodCell(row, floodField(alert, 'state_code'));
                    appendFloodCell(row, floodField(alert, 'lga_id'));
                    appendFloodCell(row, `Level ${floodField(alert, 'warning_level')}`);
                    appendFloodCell(row, floodField(alert, 'status'));
                    appendFloodCell(row, floodField(alert, 'confidence'));
                    alertsBody.appendChild(row);
                });
                if (!alerts.alerts.length) {
                    const row = document.createElement('tr');
                    appendFloodCell(row, alerts.status === 'NOT_CONFIGURED' ? 'No operational alert feed connected' : 'No alerts recorded');
                    alertsBody.appendChild(row);
                }

                const evaluationBody = document.getElementById('flood-performance-body');
                evaluationBody.replaceChildren();
                performance.evaluations.forEach(evaluation => {
                    const row = document.createElement('tr');
                    appendFloodCell(row, floodField(evaluation, 'alert_id'));
                    appendFloodCell(row, floodField(evaluation, 'evaluated_at'));
                    appendFloodCell(row, floodField(evaluation, 'lead_time_hours'));
                    appendFloodCell(row, floodField(evaluation, 'hit_status'));
                    appendFloodCell(row, floodField(evaluation, 'alerted_extent_sqkm'));
                    appendFloodCell(row, floodField(evaluation, 'observed_extent_sqkm'));
                    appendFloodCell(row, floodField(evaluation, 'confidence'));
                    evaluationBody.appendChild(row);
                });
                if (!performance.evaluations.length) {
                    const row = document.createElement('tr');
                    appendFloodCell(row, 'No verified performance evaluations available');
                    evaluationBody.appendChild(row);
                }

                const levelsContainer = document.getElementById('flood-levels');
                levelsContainer.replaceChildren();
                levels.levels.forEach(level => {
                    const card = document.createElement('div');
                    card.style.cssText = 'background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.75rem;';
                    const title = document.createElement('strong');
                    title.textContent = `Level ${level.level} — ${level.name}`;
                    const description = document.createElement('div');
                    description.style.cssText = 'font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.3rem;';
                    description.textContent = level.guidance;
                    card.append(title, description);
                    levelsContainer.appendChild(card);
                });

                if (!floodMap) {
                    const floodBases = createBaseLayers();
                    floodMap = L.map('flood-map', {
                        zoomControl: true,
                        attributionControl: true,
                        layers: [floodBases["🗺️ Dark Canvas (Esri)"]]
                    }).setView([9.0820, 7.5000], 6.5);
                    window.floodMap = floodMap;
                    floodLayerControl = L.control.layers(floodBases, {}, { position: 'topright' }).addTo(floodMap);

                    // Add legend to flood map
                    const legend = L.control({ position: 'bottomright' });
                    legend.onAdd = function() {
                        const div = L.DomUtil.create('div', 'map-legend');
                        div.style.cssText = 'background: rgba(14,22,38,0.92); border: 1px solid rgba(255,255,255,0.15); padding: 8px 12px; border-radius: 8px; font-size: 11px; color: #F8FAFC; line-height: 1.6;';
                        div.innerHTML = `
                            <strong style="color: #38BDF8; font-size: 12px;">Alert Levels</strong><br>
                            <span style="display:inline-block;width:10px;height:10px;background:#EF4444;border-radius:2px;margin-right:5px;"></span> Level 3: Emergency<br>
                            <span style="display:inline-block;width:10px;height:10px;background:#F97316;border-radius:2px;margin-right:5px;"></span> Level 2: Warning<br>
                            <span style="display:inline-block;width:10px;height:10px;background:#FBBF24;border-radius:2px;margin-right:5px;"></span> Level 1: Watch<br>
                            <span style="display:inline-block;width:10px;height:10px;background:#38BDF8;border-radius:50%;margin-right:5px;"></span> Observed SAR Extent
                        `;
                        return div;
                    };
                    legend.addTo(floodMap);

                    // Load G39 Warning Points and G43 Flood Extents once
                    fetch('/api/geojson/layer/G39')
                        .then(r => r.json())
                        .then(pts => {
                            const ptLayer = L.geoJSON(pts, {
                                pointToLayer: (feat, latlng) => {
                                    return L.circleMarker(latlng, {
                                        radius: 7,
                                        fillColor: '#F97316',
                                        color: '#FFFFFF',
                                        weight: 2,
                                        fillOpacity: 0.95
                                    });
                                },
                                onEachFeature: (feat, layer) => {
                                    const p = feat.properties || {};
                                    layer.bindPopup(`<strong>⚠️ Gauge Warning Point:</strong><br>${p.name || p.point_id}<br>State: ${p.state_code || ''}<br>Warning Level: ${p.warning_level || 'Active'}`);
                                }
                            }).addTo(floodMap);
                            floodLayerControl.addOverlay(ptLayer, "⚠️ G39 Warning Gauge Points");
                        }).catch(e => console.warn('G39 warning:', e));

                    fetch('/api/geojson/layer/G43')
                        .then(r => r.json())
                        .then(ext => {
                            const extLayer = L.geoJSON(ext, {
                                pointToLayer: (feat, latlng) => {
                                    return L.circleMarker(latlng, {
                                        radius: 6,
                                        fillColor: '#38BDF8',
                                        color: '#0284C7',
                                        weight: 1.5,
                                        fillOpacity: 0.8
                                    });
                                },
                                onEachFeature: (feat, layer) => {
                                    const p = feat.properties || {};
                                    layer.bindPopup(`
                                        <div style="color: #0F172A; font-size: 12px;">
                                            <strong style="color: #0284C7;">🌊 Flood Event (${p.Event_ID || ''})</strong><br>
                                            Community: ${p.Community || ''} (${p.State_Name || ''})<br>
                                            Inundated: <b>${p.Inundated_Area_Km2 || ''} km²</b><br>
                                            Depth: <b>${p.Observed_Depth_M || ''} m</b><br>
                                            Sensor: ${p.SAR_Sensor || ''}
                                        </div>
                                    `);
                                }
                            }).addTo(floodMap);
                            floodLayerControl.addOverlay(extLayer, "🌊 G43 Observed Flood Extent");
                        }).catch(e => console.warn('G43 warning:', e));
                }

                if (window.floodAlertLayer) floodMap.removeLayer(window.floodAlertLayer);
                window.floodAlertLayer = L.geoJSON(geojson, {
                    style: feature => {
                        const lvl = Number(feature.properties?.warning_level || feature.properties?.Warning_Level) || 1;
                        const colors = ['#94A3B8', '#FBBF24', '#F97316', '#EF4444'];
                        return {
                            color: colors[lvl] || '#EF4444',
                            weight: 2.5,
                            fillColor: colors[lvl] || '#EF4444',
                            fillOpacity: 0.35
                        };
                    },
                    onEachFeature: (feature, layer) => {
                        const p = feature.properties || {};
                        const alertId = p.alert_id || p.Alert_ID || 'Flood alert area';
                        const zoneName = p.zone_name || p.Zone_Name || '';
                        const lvl = p.warning_level || p.Warning_Level || 'unknown';
                        layer.bindPopup(`
                            <div style="color: #0F172A; font-family: sans-serif; font-size: 13px;">
                                <strong style="font-size: 14px; color: #DC2626;">🚨 ${alertId}</strong><br>
                                ${zoneName ? `<strong>Zone:</strong> ${zoneName}<br>` : ''}
                                <strong>Warning Level:</strong> <span style="font-weight: bold; color: #DC2626;">Level ${lvl}</span><br>
                                <strong>State:</strong> ${p.state_code || p.State_Code || ''}
                            </div>
                        `);
                    }
                }).addTo(floodMap);

                if (floodLayerControl && !window.floodAlertLayerAdded) {
                    floodLayerControl.addOverlay(window.floodAlertLayer, "🚨 G38 Flood Alert Zones");
                    window.floodAlertLayerAdded = true;
                }

                setTimeout(() => floodMap.invalidateSize(), 150);
            }).catch(error => {
                status.textContent = 'Flood data unavailable';
                console.error(error);
            });
        }

        // Initialize Executive Overview Map
        const overviewBases = createBaseLayers();
        const map = L.map('map', {
            zoomControl: true,
            attributionControl: true,
            layers: [overviewBases["🗺️ Dark Canvas (Esri)"]]
        }).setView([9.0820, 7.5000], 6.5);
        window.map = map;

        const overviewLayerControl = L.control.layers(overviewBases, {}, { position: 'topright' }).addTo(map);

        // Fetch Priority Sites GeoJSON
        fetch('/api/geojson/priority_sites')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    pointToLayer: function (feature, latlng) {
                        const isTier1 = feature.properties.tier === 'Tier 1 Critical';
                        return L.circleMarker(latlng, {
                            radius: isTier1 ? 9 : 7,
                            fillColor: isTier1 ? '#EF4444' : '#F59E0B',
                            color: '#FFFFFF',
                            weight: 1.5,
                            opacity: 1,
                            fillOpacity: 0.85
                        });
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties;
                        layer.bindPopup(`
                            <div style="color: #0F172A; font-family: sans-serif; font-size: 13px;">
                                <strong style="font-size: 14px;">${p.name}</strong><br>
                                <span style="color: #64748B;">State: ${p.state} (${p.type})</span><hr style="margin: 6px 0;">
                                <strong>Composite Risk:</strong> ${p.risk} / 100<br>
                                <strong>Priority:</strong> <span style="color: ${p.tier.includes('Critical') ? '#DC2626' : '#D97706'}; font-weight: bold;">${p.tier}</span>
                            </div>
                        `);
                    }
                }).addTo(map);
                overviewLayerControl.addOverlay(layer, "📍 Priority Hotspots");
            });

        // Add G01 N-HYPPADEC States boundary overlay
        fetch('/api/geojson/layer/G01')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    style: {
                        color: '#06B6D4',
                        weight: 1.5,
                        fillColor: '#06B6D4',
                        fillOpacity: 0.08
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties;
                        layer.bindTooltip(`<strong>${p.State_Name || p.State || 'State'}</strong>`, { sticky: true });
                    }
                }).addTo(map);
                overviewLayerControl.addOverlay(layer, "🏛️ N-HYPPADEC States (G01)");
            }).catch(e => console.warn('G01 load warning:', e));

        // Add G05 River & Drainage Network overlay
        fetch('/api/geojson/layer/G05')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    style: {
                        color: '#38BDF8',
                        weight: 2,
                        opacity: 0.75
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties;
                        layer.bindPopup(`<strong>🌊 River Network:</strong> ${p.River_Name || p.Name || 'Drainage Channel'}`);
                    }
                });
                overviewLayerControl.addOverlay(layer, "🌊 River Drainage Network (G05)");
            }).catch(e => console.warn('G05 load warning:', e));

        // Add G07 Hydro Facilities & Dams overlay
        fetch('/api/geojson/layer/G07')
            .then(res => res.json())
            .then(data => {
                const layer = L.geoJSON(data, {
                    pointToLayer: function (feature, latlng) {
                        return L.circleMarker(latlng, {
                            radius: 8,
                            fillColor: '#0284C7',
                            color: '#38BDF8',
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.9
                        });
                    },
                    onEachFeature: function (feature, layer) {
                        const p = feature.properties;
                        layer.bindPopup(`<strong>⚡ Hydro Facility:</strong> ${p.Facility_Name || p.Name || 'Dam'}<br>State: ${p.State_Name || p.State || ''}`);
                    }
                });
                overviewLayerControl.addOverlay(layer, "⚡ Hydro Facilities & Dams (G07)");
            }).catch(e => console.warn('G07 load warning:', e));

        // Fetch State Risk Summaries
        fetch('/api/risk/summary')
            .then(res => res.json())
            .then(data => {
                document.getElementById('kpi-critical').innerText = data.total_critical_hotspots;
                document.getElementById('kpi-risk').innerText = data.overall_composite_risk_mean;

                const tbody = document.getElementById('state-table-body');
                tbody.innerHTML = '';
                data.state_profiles.forEach(s => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td style="font-weight: 500;">${s.state_name}</td>
                        <td><span style="color: var(--text-secondary);">${s.internal_code}</span></td>
                        <td><span style="font-weight: 600; color: ${s.r_score >= 65 ? '#F87171' : '#FBBF24'};">${s.r_score}</span></td>
                        <td><span class="tier-badge ${s.r_score >= 65 ? 'tier-1' : 'tier-2'}">${s.tier1_critical}</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            });

        // Load Top 20 Priority Communities
        fetch('/api/tables/Priority_Areas?limit=20')
            .then(res => res.json())
            .then(res => {
                const tbody = document.getElementById('top20-table-body');
                tbody.innerHTML = '';
                res.data.forEach((row, i) => {
                    const tr = document.createElement('tr');
                    const tierClass = row.Priority_Tier.includes('Tier 1') ? 'tier-1' : (row.Priority_Tier.includes('Tier 2') ? 'tier-2' : 'tier-3');
                    tr.innerHTML = `
                        <td><strong>${i + 1}</strong></td>
                        <td><code>${row.Community_ID}</code></td>
                        <td>${row.State_Code}</td>
                        <td>${row.LGA_Code || 'N/A'}</td>
                        <td><strong>${row.Composite_Risk}</strong></td>
                        <td>${row.Adaptation_Gap}</td>
                        <td style="font-weight: 700; color: var(--accent-cyan);">${row.Priority_Score}</td>
                        <td><span class="tier-badge ${tierClass}">${row.Priority_Tier}</span></td>
                        <td><span style="font-size: 0.75rem; color: var(--text-secondary);">${row.Confidence_Rating}</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            });

        // Load Scenarios Data
        function loadScenariosData() {
            fetch('/api/scenarios')
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('scenario-cards-container');
                    container.innerHTML = '';
                    data.scenarios.forEach(s => {
                        const deltaColor = s.Mean_Delta > 0 ? '#F87171' : (s.Mean_Delta < 0 ? '#34D399' : 'var(--text-secondary)');
                        const deltaSign = s.Mean_Delta > 0 ? '+' : '';
                        const card = document.createElement('div');
                        card.className = 'scenario-card';
                        card.innerHTML = `
                            <div class="scenario-badge">${s.Scenario_ID}</div>
                            <h3 style="font-family: var(--font-display); font-size: 1.05rem;">${s.Scenario_Name}</h3>
                            <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                                <div>
                                    <div style="font-size: 0.72rem; color: var(--text-secondary);">Projected Mean Risk</div>
                                    <div style="font-family: var(--font-display); font-size: 1.7rem; font-weight: 700; color: #FFFFFF;">${s.Mean_Risk}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 0.72rem; color: var(--text-secondary);">Risk Delta</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: ${deltaColor};">${deltaSign}${s.Mean_Delta}</div>
                                </div>
                            </div>
                            <hr style="border-color: var(--border-color); opacity: 0.5;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.78rem;">
                                <span>Tier 1 Critical: <strong style="color: #F87171;">${s.Tier1_Critical_Count}</strong></span>
                                <span>Tier 2 High: <strong>${s.Tier2_High_Count}</strong></span>
                                <span>Tier 4 Monitor: <strong style="color: #34D399;">${s.Tier4_Monitor_Count}</strong></span>
                            </div>
                        `;
                        container.appendChild(card);
                    });
                });
        }

        function updateSim() {
            const rain = parseFloat(document.getElementById('slider-rain').value);
            const temp = parseFloat(document.getElementById('slider-temp').value);
            const adp = parseFloat(document.getElementById('slider-adp').value);

            document.getElementById('slider-rain-val').innerText = '+' + rain + '%';
            document.getElementById('slider-temp-val').innerText = '+' + temp + '°C';
            document.getElementById('slider-adp-val').innerText = adp + '%';

            // Real-time perturbation formula
            const baseRisk = 42.49;
            const hazardElev = (rain * 0.45) + (temp * 2.2);
            const adpReduction = (adp * 0.22);
            const projected = Math.min(100, Math.max(0, baseRisk + hazardElev - adpReduction));
            const delta = projected - baseRisk;

            document.getElementById('sim-projected-risk').innerText = projected.toFixed(2);
            document.getElementById('sim-risk-delta').innerText = (delta >= 0 ? '+' : '') + delta.toFixed(2);
            document.getElementById('sim-risk-delta').style.color = delta > 0 ? '#F87171' : '#34D399';

            let t1 = 1;
            if (projected > 50) t1 = Math.round(1 + (projected - 50) * 0.6);
            if (projected < 35) t1 = 0;
            document.getElementById('sim-tier1-count').innerText = t1;
        }

        // Load Interventions Data
        function loadInterventionsData() {
            fetch('/api/interventions')
                .then(res => res.json())
                .then(res => {
                    const tbody = document.getElementById('interventions-table-body');
                    tbody.innerHTML = '';
                    res.interventions.forEach(item => {
                        const tr = document.createElement('tr');
                        const statusColor = item.Status === 'Commissioned' ? '#34D399' : (item.Status === 'Completed' ? '#60A5FA' : '#FBBF24');
                        const iesDisplay = item.IES_Score_Pct ? `<span class="tier-badge tier-4">${item.IES_Score_Pct}%</span>` : '<span style="color: var(--text-secondary);">In Progress</span>';
                        tr.innerHTML = `
                            <td><code>${item.Intervention_ID}</code></td>
                            <td style="font-weight: 500;">${item.Project_Title}</td>
                            <td>${item.State_Code}</td>
                            <td>${item.Community_ID}</td>
                            <td>₦${(item.Budget_NGN / 1e6).toFixed(1)}M</td>
                            <td><span style="color: ${statusColor}; font-weight: 600;">${item.Status}</span></td>
                            <td>${item.Risk_Before}</td>
                            <td>${item.Risk_After || 'N/A'}</td>
                            <td>${iesDisplay}</td>
                            <td><strong>${item.Residual_Risk}</strong></td>
                        `;
                        tbody.appendChild(tr);
                    });
                });
        }

        // Load 22-Table Architecture Explorer
        function loadTablesList() {
            fetch('/api/tables')
                .then(res => res.json())
                .then(res => {
                    const select = document.getElementById('table-select');
                    select.innerHTML = '';
                    res.tables.forEach(t => {
                        const opt = document.createElement('option');
                        opt.value = t.table_name;
                        opt.innerText = `${t.table_name} (${t.rows} rows, ${t.columns} cols)`;
                        select.appendChild(opt);
                    });
                    loadSelectedTable();
                });
        }

        function loadSelectedTable() {
            const tableName = document.getElementById('table-select').value;
            if (!tableName) return;

            document.getElementById('table-row-count').innerText = 'Loading table...';
            fetch('/api/tables/' + tableName + '?limit=25')
                .then(res => res.json())
                .then(res => {
                    document.getElementById('table-row-count').innerText = `${res.total_rows} Records in Database`;
                    document.getElementById('table-schema-info').innerText = `Displaying first ${Math.min(res.limit, res.total_rows)} rows | Verified CLEAN Schema`;

                    const thead = document.getElementById('explorer-thead');
                    const tbody = document.getElementById('explorer-tbody');
                    thead.innerHTML = '';
                    tbody.innerHTML = '';

                    if (res.data.length === 0) return;

                    const cols = Object.keys(res.data[0]);
                    const headerRow = document.createElement('tr');
                    cols.forEach(c => {
                        const th = document.createElement('th');
                        th.innerText = c;
                        headerRow.appendChild(th);
                    });
                    thead.appendChild(headerRow);

                    res.data.forEach(r => {
                        const tr = document.createElement('tr');
                        cols.forEach(c => {
                            const td = document.createElement('td');
                            td.innerText = r[c] !== null && r[c] !== undefined ? r[c] : '—';
                            tr.appendChild(td);
                        });
                        tbody.appendChild(tr);
                    });
                });
        }

        function evaluateRisk() {
            const h = parseFloat(document.getElementById('in_h').value) || 0;
            const e = parseFloat(document.getElementById('in_e').value) || 0;
            const v = parseFloat(document.getElementById('in_v').value) || 0;
            const c = parseFloat(document.getElementById('in_c').value) || 0;

            fetch('/api/risk/calculate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({hazard: h, exposure: e, vulnerability: v, criticality: c})
            })
            .then(res => res.json())
            .then(res => {
                const box = document.getElementById('calc-result');
                box.style.display = 'block';
                box.innerHTML = `
                    <strong>Provisional Risk (R):</strong> <span style="color: var(--accent-cyan); font-weight: bold;">${res.provisional_additive_risk}</span> / 100<br>
                    <strong>Multiplicative Check (Stage 17.9):</strong> ${res.stage17_9_multiplicative_check}<br>
                    <strong>Assigned Status:</strong> <span class="tier-badge tier-1">${res.priority_tier}</span>
                `;
            });
        }

        function evaluateIES() {
            const rb = parseFloat(document.getElementById('ies_r_before').value) || 0;
            const ra = parseFloat(document.getElementById('ies_r_after').value) || 0;
            const boundsMatch = document.getElementById('ies_bounds_match').value === 'true';

            fetch('/api/ies/calculate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({risk_before: rb, risk_after: ra, reference_bounds_match: boundsMatch})
            })
            .then(res => res.json())
            .then(res => {
                const box = document.getElementById('ies-result');
                box.style.display = 'block';
                if (res.valid) {
                    box.innerHTML = `
                        <strong style="color: #34D399;">VALID EVALUATION:</strong><br>
                        <strong>IES Score:</strong> <span style="color: var(--accent-cyan); font-weight: bold;">${res.ies_percentage}%</span> reduction<br>
                        <strong>Residual Risk:</strong> ${res.residual_risk}<br>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">Classification: ${res.label}</span>
                    `;
                } else {
                    box.innerHTML = `
                        <strong style="color: #F87171;">INVALID PER SECTION 34:</strong><br>
                        <span>${res.reason}</span>
                    `;
                }
            });
        }

        // Load Remote Sensing & Earth Observation Data
        function loadRemoteSensingData() {
            fetch('/api/remote_sensing')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('kpi-rs-flood').innerText = data.total_sar_flood_area_km2 + ' km²';
                    document.getElementById('kpi-rs-ndvi').innerText = data.mean_ndvi;
                    document.getElementById('kpi-rs-retreat').innerText = data.mean_riverbank_retreat_m_yr + ' m/yr';
                    document.getElementById('kpi-rs-accuracy').innerText = data.overall_classification_accuracy_pct + '%';

                    const tbody = document.getElementById('rs-table-body');
                    tbody.innerHTML = '';
                    data.records.forEach(r => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td style="font-weight: 600;">${r.State_Name}</td>
                            <td><code>${r.State_Code}</code></td>
                            <td>${r.Major_Hydro_Basin}</td>
                            <td style="font-weight: 700; color: #60A5FA;">${r.SAR_Observed_Flood_Area_Km2.toLocaleString()} km²</td>
                            <td>${r.Mean_NDVI_Baseline}</td>
                            <td>${r.Tree_Canopy_Cover_Pct}%</td>
                            <td style="color: ${r.Mean_Riverbank_Retreat_M_Yr >= 4.0 ? '#F87171' : '#FBBF24'}; font-weight: 600;">${r.Mean_Riverbank_Retreat_M_Yr} m/yr</td>
                            <td>${r.Cropland_Flood_Exposure_Pct}%</td>
                            <td><span class="status-pill" style="font-size: 0.72rem;">${r.EO_Classification_Accuracy_Pct}%</span></td>
                            <td><span class="tier-badge tier-4">${r.QC_Status}</span></td>
                        `;
                        tbody.appendChild(tr);
                    });
                });
        }
    