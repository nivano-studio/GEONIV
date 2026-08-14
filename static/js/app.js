/**
 * GEONIV OSINT & GEOINT 3D - Lógica Frontend
 * Análise Forense EXIF, Pivôs Geográficos (Street View, Google Earth, SunCalc),
 * Calculador Geodésico e Inteligência de Rede & IP OSINT.
 */

document.addEventListener('DOMContentLoaded', () => {
    let boxesData = [];
    let selectedBox = null;
    let map2D = null;
    let markersGroup2D = null;
    let engine3D = null;

    // 1. Inicializar Motor 3D Three.js
    if (window.Geoniv3DEngine) {
        try {
            engine3D = new window.Geoniv3DEngine('threeCanvasContainer');
            window.onSelectBoxFrom3D = (boxData) => {
                openBox3DInspectorModal(boxData);
            };
        } catch (e) {
            console.warn('Erro ao inicializar Three.js Engine:', e);
        }
    }

    // 2. Inicializar Mapa 2D Leaflet
    initLeaflet2DMap();

    // 3. Carregar Histórico Salvo no Navegador (localStorage)
    renderLocalStorageHistory();

    // 4. Inicializar Eventos
    setupTabSwitching();
    setupDropzone();
    setupSearchFilter();
    setupFormEvents();
    setupGeodesicCalculator();
    setupNetworkOsintTools();
    setupPhoneOsintTools();
    setupOsintHub();

    // 5. Carregar Registros OSINT via API
    fetchAndRenderBoxes();

    /* =========================================================================
       MAPA LEAFLET 2D
       ========================================================================= */
    function initLeaflet2DMap() {
        const mapEl = document.getElementById('map');
        if (!mapEl) return;

        const defaultLat = -23.55052;
        const defaultLng = -46.633308;

        try {
            map2D = L.map('map', { 
                zoomControl: false,
                maxZoom: 21
            }).setView([defaultLat, defaultLng], 16);
            
            L.control.zoom({ position: 'topleft' }).addTo(map2D);

            const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                maxZoom: 21,
                maxNativeZoom: 18,
                attribution: 'Esri Satellite HD'
            });

            const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 21,
                maxNativeZoom: 19,
                attribution: 'OpenStreetMap'
            });

            satelliteLayer.addTo(map2D);
            markersGroup2D = L.layerGroup().addTo(map2D);

            const btnSat = document.getElementById('btnSatellite');
            const btnStreet = document.getElementById('btnStreet');

            btnSat?.addEventListener('click', () => {
                map2D.removeLayer(streetLayer);
                satelliteLayer.addTo(map2D);
                btnSat.classList.add('active');
                btnStreet.classList.remove('active');
            });

            map2D.on('click', (e) => {
                const clickedLat = e.latlng.lat;
                const clickedLng = e.latlng.lng;

                if (selectedBox) {
                    selectedBox.latitude = clickedLat;
                    selectedBox.longitude = clickedLng;
                    selectedBox.is_inferred_gps = true;
                    saveUploadToLocalStorage(selectedBox);
                    fetchAndRenderBoxes();
                    showToast(`📍 Ponto fixado no mapa: ${clickedLat.toFixed(4)}, ${clickedLng.toFixed(4)} para ${selectedBox.code}!`, 'success');
                } else {
                    showToast(`💡 Coordenadas clicadas: ${clickedLat.toFixed(5)}, ${clickedLng.toFixed(5)}`, 'info');
                }
            });
        } catch (e) {
            console.warn('Erro ao inicializar Leaflet:', e);
        }
    }

    /* =========================================================================
       TOAST NOTIFICATIONS (FEEDBACK VISUAL INSTANTÂNEO)
       ========================================================================= */
    function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            if (!container) return;

            const toast = document.createElement('div');
            toast.className = `toast-msg toast-${type}`;
            
            let icon = 'fa-info-circle';
            if (type === 'success') icon = 'fa-circle-check';
            if (type === 'warning') icon = 'fa-triangle-exclamation';
            if (type === 'error') icon = 'fa-circle-xmark';

            toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
            container.appendChild(toast);

            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100px)';
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, 4500);
        }

        /* =========================================================================
           HISTÓRICO SALVO NO NAVEGADOR (LOCALSTORAGE & ZERO-DATABASE)
           ========================================================================= */
        function getLocalCustomRecords() {
            try {
                const raw = localStorage.getItem('geoniv_custom_records');
                return raw ? JSON.parse(raw) : [];
            } catch (e) {
                return [];
            }
        }

        function saveLocalCustomRecord(record) {
            try {
                const list = getLocalCustomRecords();
                const existingIdx = list.findIndex(r => r.id === record.id);
                if (existingIdx >= 0) {
                    list[existingIdx] = record;
                } else {
                    list.unshift(record);
                }
                localStorage.setItem('geoniv_custom_records', JSON.stringify(list));
            } catch (e) {
                console.warn('Erro ao salvar registro local:', e);
            }
        }

        function saveUploadToLocalStorage(fileData) {
            try {
                const record = {
                    id: fileData.id,
                    filename: fileData.filename || fileData.title || 'Imagem enviada',
                    code: fileData.code || 'GEO-001',
                    date: fileData.date_added || new Date().toLocaleString(),
                    latitude: fileData.latitude,
                    longitude: fileData.longitude,
                    camera_info: fileData.camera_info || 'Não informada',
                    software: fileData.software,
                    photo_thumbnail: fileData.photo_thumbnail,
                    timestamp: new Date().getTime()
                };
                localStorage.setItem('geoniv_last_upload', JSON.stringify(record));
                saveLocalCustomRecord(fileData);
                renderLocalStorageHistory();
            } catch (e) {
                console.warn('Erro ao salvar no localStorage:', e);
            }
        }

        function saveSearchToLocalStorage(query) {
            try {
                if (query && query.trim() !== '') {
                    localStorage.setItem('geoniv_last_search', query.trim());
                    renderLocalStorageHistory();
                }
            } catch (e) {
                console.warn('Erro ao salvar busca no localStorage:', e);
            }
        }

        function renderLocalStorageHistory() {
            const infoContainer = document.getElementById('lastUploadInfo');
            const searchContainer = document.getElementById('lastSearchInfo');
            if (!infoContainer) return;

            const rawUpload = localStorage.getItem('geoniv_last_upload');
            if (rawUpload) {
                try {
                    const upload = JSON.parse(rawUpload);
                    const hasGps = upload.latitude && upload.longitude;
                    const gmapsUrl = hasGps ? `https://www.google.com/maps?q=${upload.latitude},${upload.longitude}` : '#';

                    infoContainer.innerHTML = `
                        <div class="history-item-row">
                            <span>Arquivo:</span>
                            <span class="history-filename">${upload.filename}</span>
                        </div>
                        <div class="history-item-row">
                            <span>Código:</span>
                            <strong>${upload.code}</strong>
                        </div>
                        <div class="history-item-row">
                            <span>Câmera:</span>
                            <span>${upload.camera_info}</span>
                        </div>
                        <div class="history-item-row">
                            <span>Data:</span>
                            <span>${upload.date}</span>
                        </div>
                        ${hasGps ? `
                        <div style="margin-top: 6px;">
                            <a href="${gmapsUrl}" target="_blank" class="btn-gmaps-mini" style="display: inline-flex; width: 100%; justify-content: center;">
                                📍 Ver no Google Maps (${Number(upload.latitude).toFixed(4)}, ${Number(upload.longitude).toFixed(4)})
                            </a>
                        </div>
                        ` : '<div style="margin-top: 4px; color: var(--accent-amber); font-size: 11px;">Sem GPS EXIF no arquivo</div>'}
                    `;
                } catch (e) {
                    infoContainer.innerHTML = `<p class="history-empty"><i class="fa-solid fa-info-circle"></i> Nenhum registro recente salvo.</p>`;
                }
            } else {
                infoContainer.innerHTML = `<p class="history-empty"><i class="fa-solid fa-info-circle"></i> Nenhum upload recente salvo no navegador.</p>`;
            }

            const lastSearch = localStorage.getItem('geoniv_last_search');
            if (searchContainer) {
                if (lastSearch) {
                    searchContainer.innerHTML = `
                        <div style="margin-top: 6px; font-size: 11px;">
                            <span>Última Pesquisa:</span> <span class="search-badge">${lastSearch}</span>
                        </div>
                    `;
                } else {
                    searchContainer.innerHTML = '';
                }
            }
        }

        /* =========================================================================
           CARREGAR E RENDERIZAR ALVOS (COMBINA SERVIDOR + LOCALSTORAGE)
           ========================================================================= */
        async function fetchAndRenderBoxes() {
            let serverRecords = [];
            try {
                const response = await fetch('/api/boxes');
                if (response.ok) {
                    serverRecords = await response.json();
                }
            } catch (error) {
                console.warn('Servidor offline ou sem resposta, usando dados locais:', error);
            }

            const localRecords = getLocalCustomRecords();
            
            // Mesclar evitando duplicados por ID
            const mergedMap = new Map();
            localRecords.forEach(r => mergedMap.set(r.id, r));
            serverRecords.forEach(r => {
                if (!mergedMap.has(r.id)) {
                    mergedMap.set(r.id, r);
                }
            });

            boxesData = Array.from(mergedMap.values());

            renderBoxesList(boxesData);
            renderBoxes2DMap(boxesData);
            if (engine3D) engine3D.renderBoxesIn3DTerrain(boxesData);
            updateDashboardMetrics(boxesData);
            populateGeodesicSelects(boxesData);
        }

    function renderBoxesList(boxes) {
        const listContainer = document.getElementById('boxesList');
        if (!listContainer) return;

        if (!boxes || boxes.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-folder-open" style="font-size: 32px; color: var(--text-muted); margin-bottom: 8px;"></i>
                    <p>Nenhum alvo ou arquivo mapeado ainda.</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = '';
        boxes.forEach(box => {
            const item = document.createElement('div');
            item.className = `box-item ${selectedBox?.id === box.id ? 'selected' : ''}`;
            
            const hasGps = box.latitude !== null && box.latitude !== undefined && box.longitude !== null && box.longitude !== undefined;
            const gmapsUrl = hasGps ? `https://www.google.com/maps?q=${box.latitude},${box.longitude}` : '#';
            const displayTitle = box.filename || box.title || box.code;

            // Selo por Categoria de Arquivo
            let categoryBadge = '';
            const cat = box.category || 'image';
            if (cat === 'pdf') {
                categoryBadge = `<span class="cat-badge badge-pdf"><i class="fa-solid fa-file-pdf"></i> PDF</span>`;
            } else if (cat === 'document') {
                categoryBadge = `<span class="cat-badge badge-doc"><i class="fa-solid fa-file-word"></i> DOC</span>`;
            } else if (cat === 'audio') {
                categoryBadge = `<span class="cat-badge badge-audio"><i class="fa-solid fa-file-audio"></i> ÁUDIO</span>`;
            } else if (cat === 'video') {
                categoryBadge = `<span class="cat-badge badge-video"><i class="fa-solid fa-file-video"></i> VÍDEO</span>`;
            } else {
                categoryBadge = `<span class="cat-badge badge-img"><i class="fa-solid fa-image"></i> FOTO</span>`;
            }

            // Prévia de Endereço Reverso
            let addressLine = '';
            if (box.address && box.address.display_name) {
                const addr = box.address;
                const cityStr = addr.city || addr.state || addr.country || '';
                const roadStr = addr.road || addr.suburb || '';
                const fullStr = [roadStr, cityStr].filter(Boolean).join(', ');
                if (fullStr) {
                    addressLine = `<p class="address-preview-line"><i class="fa-solid fa-building"></i> ${fullStr}</p>`;
                }
            }

            const latNum = Number(box.latitude);
            const lngNum = Number(box.longitude);

            item.innerHTML = `
                <div class="box-item-info">
                    <h4>
                        <i class="fa-solid fa-crosshairs" style="color: var(--accent-cyan);"></i> ${box.code || 'GEO'} 
                        ${categoryBadge}
                        <span class="species-tag" style="font-family: var(--font-code);">${displayTitle}</span>
                    </h4>
                    <p><i class="fa-solid fa-location-dot"></i> ${hasGps ? `${latNum.toFixed(5)}, ${lngNum.toFixed(5)} ${box.is_inferred_gps ? '(Inferido)' : ''}` : 'Sem GPS'}</p>
                    ${addressLine}
                </div>
                <div class="box-item-actions">
                    ${hasGps ? `<a href="${gmapsUrl}" target="_blank" class="btn-gmaps-mini" title="Abrir no Google Maps" onclick="event.stopPropagation();">
                        <i class="fa-solid fa-map-pin"></i> Maps
                    </a>` : ''}
                    <button class="btn btn-sm btn-accent inspect-3d-btn" title="Inspecionar Forense">
                        <i class="fa-solid fa-microscope"></i>
                    </button>
                </div>
            `;

            item.addEventListener('click', () => {
                selectedBox = box;
                openBox3DInspectorModal(box);
            });

            listContainer.appendChild(item);
        });
    }

    function renderBoxes2DMap(boxes) {
        if (!markersGroup2D || !map2D) return;
        markersGroup2D.clearLayers();

        const latLngs = [];

        boxes.forEach(box => {
            if (box.latitude !== null && box.latitude !== undefined && box.longitude !== null && box.longitude !== undefined) {
                const lat = Number(box.latitude);
                const lng = Number(box.longitude);
                const marker = L.marker([lat, lng]).addTo(markersGroup2D);
                const gmapsUrl = `https://www.google.com/maps?q=${lat},${lng}`;
                const title = box.filename || box.title || box.code;

                const popupContent = `
                    <div style="font-family: Outfit, sans-serif; color: #0f172a; padding: 4px; min-width: 220px;">
                        <h3 style="margin: 0; font-size: 15px; color: #0f172a;">${box.code} - ${title}</h3>
                        <p style="margin: 4px 0; font-size: 11px; color: #475569;"><strong>GPS:</strong> ${lat.toFixed(6)}, ${lng.toFixed(6)}</p>
                        ${box.address && box.address.display_name ? `<p style="margin: 2px 0; font-size: 10px; color: #0284c7;">📍 ${box.address.display_name}</p>` : ''}
                        <div style="display: flex; gap: 6px; margin-top: 8px;">
                            <a href="${gmapsUrl}" target="_blank" style="flex: 1; background: #1a73e8; color: #fff; text-align: center; text-decoration: none; padding: 6px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; display: inline-block;">
                                📍 Google Maps
                            </a>
                            <button onclick="window.onSelectBoxFrom3DById('${box.id}')" style="background: #0284c7; color: #fff; border: none; padding: 6px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; cursor: pointer;">
                                🎲 Forense 3D
                            </button>
                        </div>
                    </div>
                `;

                marker.bindPopup(popupContent);
                latLngs.push([lat, lng]);
            }
        });

        if (latLngs.length > 0) {
            map2D.fitBounds(latLngs, { padding: [50, 50], maxZoom: 16 });
        }
    }

    window.onSelectBoxFrom3DById = (boxId) => {
        const box = boxesData.find(b => b.id === boxId);
        if (box) openBox3DInspectorModal(box);
    };

    function updateDashboardMetrics(boxes) {
        const total = boxes.length;
        const withGps = boxes.filter(b => b.has_gps && b.latitude && b.longitude).length;
        
        let cameraCount = 0;
        let pdfCount = 0;
        let docCount = 0;
        let mediaCount = 0;

        const cameraSet = new Set();
        boxes.forEach(b => {
            if (b.camera_info && b.camera_info !== 'Cadastro Manual' && b.camera_info !== 'Não informada' && !b.camera_info.startsWith('Arquivo') && !b.camera_info.startsWith('PDF') && !b.camera_info.startsWith('Office')) {
                cameraSet.add(b.camera_info);
            }

            const cat = b.category || 'image';
            if (cat === 'pdf') pdfCount++;
            else if (cat === 'document') docCount++;
            else if (cat === 'audio' || cat === 'video') mediaCount++;
        });

        const dashTotal = document.getElementById('dashTotalBoxes');
        const dashGps = document.getElementById('dashGpsBoxes');
        const dashCam = document.getElementById('dashCameraCount');
        const dashKml = document.getElementById('dashKmlCount');

        if (dashTotal) dashTotal.innerText = total;
        if (dashGps) dashGps.innerText = `${withGps} (${total > 0 ? Math.round((withGps / total) * 100) : 0}%)`;
        if (dashCam) dashCam.innerText = cameraSet.size > 0 ? `${cameraSet.size} Câmera(s)` : `${pdfCount + docCount + mediaCount} Outros Arquivos`;
        if (dashKml) dashKml.innerText = `${withGps} Pontos em KML`;
    }

    /* =========================================================================
       INSPETOR 3D & PIVÔS DE INVESTIGAÇÃO OSINT MULTI-ARQUIVO
       ========================================================================= */
    function openBox3DInspectorModal(box) {
        selectedBox = box;

        document.getElementById('modalBoxId').value = box.id || '';
        document.getElementById('modalCode').value = box.code || '';
        document.getElementById('modalTitle').value = box.filename || box.title || '';
        document.getElementById('modalAltitude').value = box.altitude !== null && box.altitude !== undefined ? box.altitude : '';
        document.getElementById('modalLat').value = box.latitude !== null && box.latitude !== undefined ? box.latitude : '';
        document.getElementById('modalLng').value = box.longitude !== null && box.longitude !== undefined ? box.longitude : '';
        document.getElementById('modalNotes').value = box.notes || '';

        // Foto vs 3D Preview
        const imgEl = document.getElementById('inspectorPhotoImg');
        const photoCanvas = document.getElementById('inspectorPhotoCanvas');
        const canvas3D = document.getElementById('inspector3DCanvas');
        const controls3D = document.getElementById('inspector3DControls');
        const tab3D = document.getElementById('tabShow3D');
        const tabPhoto = document.getElementById('tabShowPhoto');

        const photoSrc = box.photo_thumbnail || box.photo_url;
        if (photoSrc && imgEl && photoCanvas) {
            imgEl.src = photoSrc;
            tabPhoto.style.display = 'inline-flex';
            // Se for imagem com foto válida, abre no preview da foto
            photoCanvas.style.display = 'flex';
            canvas3D.style.display = 'none';
            if (controls3D) controls3D.style.display = 'none';
            tabPhoto.classList.add('active');
            tab3D.classList.remove('active');
        } else {
            tabPhoto.style.display = 'none';
            photoCanvas.style.display = 'none';
            canvas3D.style.display = 'block';
            if (controls3D) controls3D.style.display = 'block';
            tab3D.classList.add('active');
            tabPhoto.classList.remove('active');
        }

        tab3D?.addEventListener('click', () => {
            tab3D.classList.add('active');
            tabPhoto.classList.remove('active');
            canvas3D.style.display = 'block';
            photoCanvas.style.display = 'none';
            if (controls3D) controls3D.style.display = 'block';
            if (engine3D) engine3D.onResize();
        });

        tabPhoto?.addEventListener('click', () => {
            tabPhoto.classList.add('active');
            tab3D.classList.remove('active');
            canvas3D.style.display = 'none';
            photoCanvas.style.display = 'flex';
            if (controls3D) controls3D.style.display = 'none';
        });

        saveUploadToLocalStorage(box);

        // 1. PIVÔS GEOGRÁFICOS DE MAPA (GOOGLE MAPS, STREET VIEW, SUN CALC)
        const gmapsContainer = document.getElementById('modalGmapsAction');
        const hasGps = box.latitude !== null && box.latitude !== undefined && box.longitude !== null && box.longitude !== undefined;

        if (hasGps && gmapsContainer) {
            const lat = Number(box.latitude);
            const lng = Number(box.longitude);

            const gmapsUrl = `https://www.google.com/maps?q=${lat},${lng}`;
            const streetViewUrl = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lng}`;
            const earthUrl = `https://earth.google.com/web/@${lat},${lng},100a,35d,35y,0h,0t,0r`;
            const suncalcUrl = `https://www.suncalc.org/#/${lat},${lng},18/date/time`;

            gmapsContainer.innerHTML = `
                <div class="gmaps-box-header">
                    <span class="gmaps-box-title"><i class="fa-solid fa-satellite"></i> Pivôs de Investigação Geográfica OSINT</span>
                    <span style="font-size: 11px; color: var(--accent-emerald); font-weight: 700;">GPS OK ${box.is_inferred_gps ? '(Coordenada Inferida)' : ''}</span>
                </div>
                <div class="gmaps-btn-group">
                    <a href="${gmapsUrl}" target="_blank" class="btn-gmaps">
                        <i class="fa-solid fa-map-pin"></i> Google Maps
                    </a>
                    <a href="${streetViewUrl}" target="_blank" class="btn-streetview">
                        <i class="fa-solid fa-street-view"></i> Street View 360°
                    </a>
                    <a href="${earthUrl}" target="_blank" class="btn-gearth">
                        <i class="fa-solid fa-earth-americas"></i> Google Earth 3D
                    </a>
                    <a href="${suncalcUrl}" target="_blank" class="btn-suncalc">
                        <i class="fa-solid fa-sun"></i> SunCalc Sombras
                    </a>
                    <button type="button" class="btn-locate" id="btnFocusMap">
                        <i class="fa-solid fa-crosshairs"></i> Centralizar no Mapa 2D/3D
                    </button>
                </div>
            `;

            document.getElementById('btnFocusMap')?.addEventListener('click', () => {
                focusOnLocation(lat, lng);
                document.getElementById('box3DInspectorModal')?.classList.remove('active');
            });
        } else if (gmapsContainer) {
            const scrub = box.scrubbing_analysis || {};
            const explanation = scrub.explanation || 'Arquivos enviados pelo WhatsApp, redes sociais, prints ou PDFs sem CEP/coordenadas textuais não armazenam o chip de GPS de satélite por padrão.';
            const source = scrub.scrubbing_source ? ` (${scrub.scrubbing_source})` : '';

            gmapsContainer.innerHTML = `
                <div class="gmaps-box-header" style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px; color: var(--accent-amber); font-weight: 700; font-size: 13px;">
                        <i class="fa-solid fa-triangle-exclamation"></i> Coordenadas GPS de Satélite Ausentes${source}
                    </div>
                    <p style="font-size: 12px; color: var(--text-primary); margin-top: 6px; line-height: 1.4;">
                        ${explanation}
                    </p>
                    <div style="font-size: 11px; color: var(--accent-cyan); margin-top: 8px;">
                        💡 <strong>Como geolocalizar este alvo:</strong> Use o campo de <strong>Busca de Local/Endereço</strong> acima, clique em qualquer ponto do <strong>Mapa 2D</strong>, ou use os botões de <strong>Busca Visual por IA</strong> abaixo!
                    </div>
                </div>
            `;
        }

        // 2. ENDEREÇO GEOCODIFICADO REVERSO (NOMINATIM / OSM)
        const addressBox = document.getElementById('modalAddressInfo');
        if (addressBox) {
            if (box.address && box.address.success) {
                const addr = box.address;
                addressBox.style.display = 'block';
                addressBox.innerHTML = `
                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                        <i class="fa-solid fa-location-dot"></i> Endereço Completo Geocodificado (Nominatim/OSM)
                    </div>
                    <p style="font-size: 13px; color: var(--text-primary); margin-bottom: 6px;"><strong>${addr.display_name}</strong></p>
                    <div class="address-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; font-size: 11px;">
                        ${addr.road ? `<div><span>Logradouro:</span> <strong>${addr.road}</strong></div>` : ''}
                        ${addr.suburb ? `<div><span>Bairro:</span> <strong>${addr.suburb}</strong></div>` : ''}
                        ${addr.city ? `<div><span>Cidade:</span> <strong>${addr.city}</strong></div>` : ''}
                        ${addr.state ? `<div><span>Estado:</span> <strong>${addr.state}</strong></div>` : ''}
                        ${addr.country ? `<div><span>País:</span> <strong>${addr.country}</strong></div>` : ''}
                        ${addr.postcode ? `<div><span>CEP:</span> <strong>${addr.postcode}</strong></div>` : ''}
                    </div>
                `;
            } else {
                addressBox.style.display = 'none';
            }
        }

        // 3. METADADOS ESPECÍFICOS DO ARQUIVO (IMAGEM, PDF, OFFICE, MÍDIA)
        const exifBox = document.getElementById('modalExifInfo');
        if (exifBox) {
            const cat = box.category || 'image';
            const spec = box.specific_metadata || {};

            let exifHtml = '';

            if (cat === 'pdf') {
                exifHtml = `
                    <div class="exif-header-title"><i class="fa-solid fa-file-pdf" style="color: #ef4444;"></i> Metadados Forenses do Documento PDF</div>
                    <div class="exif-row"><span>Título:</span> <span class="exif-val">${spec.title || 'Não especificado'}</span></div>
                    <div class="exif-row"><span>Autor:</span> <span class="exif-val">${spec.author || 'Não especificado'}</span></div>
                    <div class="exif-row"><span>Assunto:</span> <span class="exif-val">${spec.subject || 'Não especificado'}</span></div>
                    <div class="exif-row"><span>Software Criador:</span> <span class="exif-val">${spec.creator || spec.producer || 'Desconhecido'}</span></div>
                    <div class="exif-row"><span>Total de Páginas:</span> <span class="exif-val"><strong>${spec.pages_count || 0} págs</strong></span></div>
                    <div class="exif-row"><span>Data de Criação:</span> <span class="exif-val">${spec.creation_date || box.date_added || 'N/A'}</span></div>
                    <div class="exif-row"><span>Criptografado:</span> <span class="exif-val">${spec.is_encrypted ? 'Sim (Protegido)' : 'Não'}</span></div>
                `;
            } else if (cat === 'document') {
                exifHtml = `
                    <div class="exif-header-title"><i class="fa-solid fa-file-word" style="color: #2563eb;"></i> Metadados do Documento Office (${box.filename})</div>
                    <div class="exif-row"><span>Título:</span> <span class="exif-val">${spec.title || 'Não especificado'}</span></div>
                    <div class="exif-row"><span>Autor / Criador:</span> <span class="exif-val">${spec.author || 'Não especificado'}</span></div>
                    <div class="exif-row"><span>Último Modificador:</span> <span class="exif-val">${spec.last_modified_by || 'N/A'}</span></div>
                    <div class="exif-row"><span>Software Aplicação:</span> <span class="exif-val">${spec.application || 'Microsoft Office / LibreOffice'}</span></div>
                    ${spec.words_count ? `<div class="exif-row"><span>Contagem de Palavras:</span> <span class="exif-val">${spec.words_count} palavras</span></div>` : ''}
                    ${spec.pages_count ? `<div class="exif-row"><span>Páginas / Slides:</span> <span class="exif-val">${spec.pages_count}</span></div>` : ''}
                    <div class="exif-row"><span>Data de Criação:</span> <span class="exif-val">${spec.creation_date || box.date_added || 'N/A'}</span></div>
                `;
            } else if (cat === 'audio' || cat === 'video') {
                exifHtml = `
                    <div class="exif-header-title"><i class="fa-solid fa-${cat === 'video' ? 'film' : 'music'}" style="color: #a855f7;"></i> Metadados de Mídia (${cat.toUpperCase()})</div>
                    <div class="exif-row"><span>Tipo de Mídia:</span> <span class="exif-val">${spec.media_type || cat.toUpperCase()}</span></div>
                    <div class="exif-row"><span>Formato:</span> <span class="exif-val">${spec.format || 'N/A'}</span></div>
                    <div class="exif-row"><span>Tamanho do Arquivo:</span> <span class="exif-val">${box.file_size || 'N/A'}</span></div>
                    <div class="exif-row"><span>Tipo MIME:</span> <span class="exif-val">${box.mime_type || 'N/A'}</span></div>
                `;
            } else {
                const isEditedTag = box.is_edited ? `<span class="forensic-warning-tag"><i class="fa-solid fa-triangle-exclamation"></i> Editado via ${box.software}</span>` : '<span style="color: var(--accent-emerald);">Sem software de edição detectado</span>';

                exifHtml = `
                    <div class="exif-header-title"><i class="fa-solid fa-camera" style="color: var(--accent-cyan);"></i> Metadados Forenses EXIF da Fotografia</div>
                    <div class="exif-row"><span>Integridade Forense:</span> <span>${isEditedTag}</span></div>
                    <div class="exif-row"><span>Dispositivo / Câmera:</span> <span class="exif-val">${box.camera_info || 'Não informada'}</span></div>
                    <div class="exif-row"><span>Data / Hora EXIF:</span> <span class="exif-val">${box.date_added || 'Não informada'}</span></div>
                    <div class="exif-row"><span>Arquivo Original:</span> <span class="exif-val">${box.filename || 'Foto enviada'}</span></div>
                    ${box.dimensions ? `<div class="exif-row"><span>Dimensões:</span> <span class="exif-val">${box.dimensions} px</span></div>` : ''}
                    ${box.iso ? `<div class="exif-row"><span>ISO:</span> <span class="exif-val">${box.iso}</span></div>` : ''}
                    ${box.aperture ? `<div class="exif-row"><span>Abertura:</span> <span class="exif-val">${box.aperture}</span></div>` : ''}
                    ${box.focal_length ? `<div class="exif-row"><span>Distância Focal:</span> <span class="exif-val">${box.focal_length}</span></div>` : ''}
                    ${box.exposure_time ? `<div class="exif-row"><span>Exposição:</span> <span class="exif-val">${box.exposure_time}</span></div>` : ''}
                    ${box.lens_model ? `<div class="exif-row"><span>Lente:</span> <span class="exif-val">${box.lens_model}</span></div>` : ''}
                `;
            }

            exifBox.innerHTML = exifHtml;
        }

        // 4. HASHES FORENSES (MD5 & SHA-256)
        const hashesBox = document.getElementById('modalHashesInfo');
        if (hashesBox) {
            if (box.hashes && (box.hashes.sha256 || box.hashes.md5)) {
                hashesBox.style.display = 'block';
                hashesBox.innerHTML = `
                    <div style="font-size: 12px; font-weight: 700; color: var(--accent-emerald); margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                        <i class="fa-solid fa-fingerprint"></i> Hashes Forenses de Integridade
                    </div>
                    <div class="hash-row" style="margin-bottom: 4px;">
                        <span style="font-size: 11px; color: var(--text-secondary);">SHA-256:</span>
                        <code style="font-size: 10px; font-family: var(--font-code); color: #38bdf8; word-break: break-all;">${box.hashes.sha256 || 'N/A'}</code>
                    </div>
                    <div class="hash-row">
                        <span style="font-size: 11px; color: var(--text-secondary);">MD5:</span>
                        <code style="font-size: 10px; font-family: var(--font-code); color: #f59e0b; word-break: break-all;">${box.hashes.md5 || 'N/A'}</code>
                    </div>
                `;
            } else {
                hashesBox.style.display = 'none';
            }
        }

        // 5. PIVÔS DE BUSCA VISUAL OSINT & DESCARTE (IMAGENS SEM GPS)
        const visualBox = document.getElementById('modalVisualOsintPivots');
        const cat = box.category || 'image';
        const scrub = box.scrubbing_analysis;

        if (visualBox) {
            if (cat === 'image') {
                visualBox.style.display = 'block';
                let vHtml = `
                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-purple); margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                        <i class="fa-solid fa-eye"></i> Investigação Visual Reversa OSINT (Imagens)
                    </div>
                `;

                if (scrub && scrub.scrubbing_detected) {
                    vHtml += `
                        <div class="scrub-warning-card" style="background: rgba(245, 158, 11, 0.1); border-left: 3px solid var(--accent-amber); padding: 8px 12px; border-radius: 6px; margin-bottom: 10px;">
                            <span style="font-weight: 700; font-size: 12px; color: var(--accent-amber);"><i class="fa-solid fa-shield-cat"></i> Origem Detectada: ${scrub.scrubbing_source}</span>
                            <p style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">${scrub.explanation}</p>
                        </div>
                    `;
                }

                if (scrub && scrub.clues_found && scrub.clues_found.length > 0) {
                    vHtml += `<div style="font-size: 11px; color: var(--accent-emerald); margin-bottom: 8px;">`;
                    scrub.clues_found.forEach(c => {
                        vHtml += `<div><i class="fa-solid fa-magnifying-glass-location"></i> ${c}</div>`;
                    });
                    vHtml += `</div>`;
                }

                vHtml += `
                    <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">Se a foto não possui coordenadas EXIF, utilize os pivôs OSINT de Busca Reversa para identificar a localização exata por correspondência de imagem:</p>
                    <div class="visual-search-btn-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px;">
                        <a href="https://yandex.com/images/search" target="_blank" class="btn-visual-pivot yandex-btn">
                            <i class="fa-solid fa-eye"></i> Yandex GEOINT
                        </a>
                        <a href="https://lens.google.com/" target="_blank" class="btn-visual-pivot lens-btn">
                            <i class="fa-brands fa-google"></i> Google Lens
                        </a>
                        <a href="https://geospy.ai/" target="_blank" class="btn-visual-pivot geospy-btn">
                            <i class="fa-solid fa-brain"></i> GeoSpy AI
                        </a>
                        <a href="https://tineye.com/" target="_blank" class="btn-visual-pivot tineye-btn">
                            <i class="fa-solid fa-robot"></i> TinEye
                        </a>
                    </div>
                `;
                visualBox.innerHTML = vHtml;
            } else {
                visualBox.style.display = 'none';
            }
        }

        const modal = document.getElementById('box3DInspectorModal');
        modal?.classList.add('active');

        const slider = document.getElementById('explodeSlider');
        if (slider) slider.value = 0;

        if (engine3D) {
            try {
                engine3D.openHive3DInspector(box);
            } catch (e) {
                console.warn('Erro ao abrir inspetor 3D:', e);
            }
        }
    }

    function focusOnLocation(lat, lng) {
        document.getElementById('tabBtn2D')?.click();
        if (map2D) {
            map2D.setView([lat, lng], 18, { animate: true });
        }
    }

    const slider = document.getElementById('explodeSlider');
    slider?.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        if (engine3D) engine3D.setExplosionFactor(val);
    });

    document.getElementById('closeInspectorModal')?.addEventListener('click', () => {
        document.getElementById('box3DInspectorModal')?.classList.remove('active');
    });

    /* =========================================================================
       FERRAMENTAS DE INTELIGÊNCIA DE REDE & IP OSINT
       ========================================================================= */
    function setupNetworkOsintTools() {
        const btnLookup = document.getElementById('btnLookupIp');
        const ipInput = document.getElementById('ipTargetInput');
        const resultContainer = document.getElementById('ipResultContainer');

        if (!btnLookup || !ipInput || !resultContainer) return;

        btnLookup.addEventListener('click', async () => {
            const query = ipInput.value.trim();
            if (!query) {
                alert('Digite um endereço IP ou domínio válido para investigar.');
                return;
            }

            resultContainer.style.display = 'block';
            resultContainer.innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--accent-cyan);">
                    <i class="fa-solid fa-spinner fa-spin" style="font-size: 28px;"></i>
                    <p style="margin-top: 10px;">Consultando geolocalização de IP, registros DNS e cabeçalhos...</p>
                </div>
            `;

            try {
                const [ipRes, dnsRes, httpRes] = await Promise.all([
                    fetch(`/api/osint/ip-lookup?target=${encodeURIComponent(query)}`),
                    fetch(`/api/osint/dns-lookup?domain=${encodeURIComponent(query)}`),
                    fetch(`/api/osint/http-headers?target=${encodeURIComponent(query)}`)
                ]);

                const ipData = await ipRes.json();
                const dnsData = await dnsRes.json();
                const httpData = await httpRes.json();

                if (ipData.status === 'fail') {
                    resultContainer.innerHTML = `<p style="color: var(--accent-red);"><i class="fa-solid fa-triangle-exclamation"></i> Falha na investigação do IP: ${ipData.message}</p>`;
                    return;
                }

                const domainName = dnsData.domain || query;
                const crtUrl = `https://crt.sh/?q=${encodeURIComponent(domainName)}`;
                const waybackUrl = `https://web.archive.org/web/*/${encodeURIComponent(domainName)}`;
                const censysUrl = `https://search.censys.io/search?q=${encodeURIComponent(domainName)}`;

                resultContainer.innerHTML = `
                    <div class="ip-result-grid">
                        <div class="ip-metric-card">
                            <span class="ip-metric-lbl">IP Resolvido:</span>
                            <span class="ip-metric-val">${ipData.query || 'N/A'}</span>
                        </div>
                        <div class="ip-metric-card">
                            <span class="ip-metric-lbl">País / Cidade:</span>
                            <span class="ip-metric-val" style="color: #60a5fa;">${ipData.city || ''}, ${ipData.country || 'N/A'}</span>
                        </div>
                        <div class="ip-metric-card">
                            <span class="ip-metric-lbl">Provedor / AS:</span>
                            <span class="ip-metric-val" style="color: var(--accent-amber); font-size: 13px;">${ipData.isp || 'N/A'}</span>
                        </div>
                        <div class="ip-metric-card">
                            <span class="ip-metric-lbl">Servidor Web:</span>
                            <span class="ip-metric-val" style="color: #38bdf8; font-size: 13px;">${httpData.server_tech || 'Oculto/CDN'}</span>
                        </div>
                    </div>

                    <div style="margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap;">
                        <button type="button" class="btn btn-accent" id="btnFocusIpOnMap">
                            📍 Localizar Servidor no Mapa 3D/2D (${ipData.lat}, ${ipData.lon})
                        </button>
                        <a href="${crtUrl}" target="_blank" class="btn-crt">
                            📜 Subdomínios (crt.sh)
                        </a>
                        <a href="${waybackUrl}" target="_blank" class="btn-wayback">
                            🏛️ Internet Archive
                        </a>
                        <a href="${censysUrl}" target="_blank" class="btn-crt" style="background: linear-gradient(135deg, #0284c7, #2563eb);">
                            🔍 Censys OSINT
                        </a>
                    </div>
                `;

                document.getElementById('btnFocusIpOnMap')?.addEventListener('click', async () => {
                    await fetchAndRenderBoxes();
                    focusOnLocation(ipData.lat, ipData.lon);
                });

                await fetchAndRenderBoxes();

            } catch (err) {
                console.error('Erro na investigação OSINT de rede:', err);
                resultContainer.innerHTML = `<p style="color: var(--accent-red);"><i class="fa-solid fa-triangle-exclamation"></i> Erro ao processar requisição de rede OSINT.</p>`;
            }
        });
    }

    /* =========================================================================
       INTELIGÊNCIA DE TELEFONIA OSINT — PHONE LOOKUP
       ========================================================================= */
    function setupPhoneOsintTools() {
        const btnLookup = document.getElementById('btnLookupPhone');
        const phoneInput = document.getElementById('phoneTargetInput');
        const resultContainer = document.getElementById('phoneResultContainer');

        if (!btnLookup || !phoneInput || !resultContainer) return;

        phoneInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') btnLookup.click();
        });

        btnLookup.addEventListener('click', async () => {
            const query = phoneInput.value.trim();
            if (!query || query.length < 7) {
                alert('Digite um número de telefone válido (mínimo 7 dígitos).');
                return;
            }

            resultContainer.style.display = 'block';
            resultContainer.innerHTML = `
                <div style="text-align: center; padding: 24px; color: var(--accent-purple);">
                    <i class="fa-solid fa-spinner fa-spin" style="font-size: 28px;"></i>
                    <p style="margin-top: 10px;">Consultando dados públicos do número...</p>
                </div>
            `;

            try {
                const res = await fetch(`/api/osint/phone-lookup?phone=${encodeURIComponent(query)}`);
                
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({ detail: 'Erro desconhecido' }));
                    resultContainer.innerHTML = `<p style="color: var(--accent-red);"><i class="fa-solid fa-triangle-exclamation"></i> ${errData.detail || 'Erro ao consultar número.'}</p>`;
                    return;
                }

                const data = await res.json();
                const dddInfo = data.ddd_info;
                const hasDdd = dddInfo && dddInfo.lat && dddInfo.lng;

                let html = `
                    <div class="phone-result-header">
                        <div class="phone-number-display">
                            <i class="fa-solid fa-phone" style="color: var(--accent-emerald);"></i>
                            <span>${data.formatted || data.input}</span>
                        </div>
                        <span class="phone-validity-badge ${data.is_valid_format ? 'valid' : 'invalid'}">
                            <i class="fa-solid fa-${data.is_valid_format ? 'circle-check' : 'triangle-exclamation'}"></i>
                            ${data.is_valid_format ? 'Formato Válido' : 'Formato Incompleto'}
                        </span>
                    </div>

                    <div class="phone-metrics-grid">
                        <div class="phone-metric-card">
                            <span class="phone-metric-icon" style="color: var(--accent-purple);"><i class="fa-solid fa-sim-card"></i></span>
                            <div class="phone-metric-data">
                                <span class="phone-metric-lbl">Tipo de Linha</span>
                                <span class="phone-metric-val">${data.line_type || 'Desconhecido'}</span>
                            </div>
                        </div>
                        <div class="phone-metric-card">
                            <span class="phone-metric-icon" style="color: var(--accent-amber);"><i class="fa-solid fa-tower-cell"></i></span>
                            <div class="phone-metric-data">
                                <span class="phone-metric-lbl">Operadora (Prefixo)</span>
                                <span class="phone-metric-val" style="font-size: 12px;">${data.carrier_hint || 'Não identificada'}</span>
                            </div>
                        </div>
                `;

                if (hasDdd) {
                    html += `
                        <div class="phone-metric-card">
                            <span class="phone-metric-icon" style="color: var(--accent-cyan);"><i class="fa-solid fa-map-location-dot"></i></span>
                            <div class="phone-metric-data">
                                <span class="phone-metric-lbl">Região do DDD ${data.ddd}</span>
                                <span class="phone-metric-val">${dddInfo.city}, ${dddInfo.uf}</span>
                            </div>
                        </div>
                        <div class="phone-metric-card">
                            <span class="phone-metric-icon" style="color: var(--accent-emerald);"><i class="fa-solid fa-earth-americas"></i></span>
                            <div class="phone-metric-data">
                                <span class="phone-metric-lbl">Coordenadas DDD</span>
                                <span class="phone-metric-val" style="font-family: var(--font-code); font-size: 12px;">${Number(dddInfo.lat).toFixed(4)}, ${Number(dddInfo.lng).toFixed(4)}</span>
                            </div>
                        </div>
                    `;
                } else if (data.ddd) {
                    html += `
                        <div class="phone-metric-card">
                            <span class="phone-metric-icon" style="color: var(--accent-amber);"><i class="fa-solid fa-triangle-exclamation"></i></span>
                            <div class="phone-metric-data">
                                <span class="phone-metric-lbl">DDD ${data.ddd}</span>
                                <span class="phone-metric-val">Região não mapeada</span>
                            </div>
                        </div>
                    `;
                }

                html += `</div>`;

                if (hasDdd) {
                    html += `
                        <div style="margin-top: 14px;">
                            <button type="button" class="btn btn-accent" id="btnFocusPhoneOnMap" style="width: 100%;">
                                <i class="fa-solid fa-crosshairs"></i> Localizar Região do DDD ${data.ddd} (${dddInfo.city}/${dddInfo.uf}) no Mapa
                            </button>
                        </div>
                    `;
                }

                if (data.osint_links && data.osint_links.length > 0) {
                    html += `
                        <div class="phone-osint-links-header">
                            <i class="fa-solid fa-magnifying-glass-arrow-right"></i>
                            Investigação OSINT — Fontes Públicas Externas
                        </div>
                        <div class="phone-osint-links-grid">
                    `;

                    data.osint_links.forEach(link => {
                        html += `
                            <a href="${link.url}" target="_blank" rel="noopener noreferrer" class="phone-osint-link-card" style="--link-color: ${link.color};">
                                <div class="phone-osint-link-icon" style="color: ${link.color};">
                                    <i class="${link.icon}"></i>
                                </div>
                                <div class="phone-osint-link-info">
                                    <span class="phone-osint-link-name">${link.name}</span>
                                    <span class="phone-osint-link-desc">${link.description}</span>
                                </div>
                                <i class="fa-solid fa-arrow-up-right-from-square phone-osint-link-arrow"></i>
                            </a>
                        `;
                    });

                    html += `</div>`;
                }

                if (data.warnings && data.warnings.length > 0) {
                    html += `<div class="phone-warnings">`;
                    data.warnings.forEach(w => {
                        html += `<div class="phone-warning-item"><i class="fa-solid fa-info-circle"></i> ${w}</div>`;
                    });
                    html += `</div>`;
                }

                resultContainer.innerHTML = html;

                if (hasDdd) {
                    document.getElementById('btnFocusPhoneOnMap')?.addEventListener('click', async () => {
                        await fetchAndRenderBoxes();
                        focusOnLocation(dddInfo.lat, dddInfo.lng);
                    });
                }

                if (data.record) {
                    await fetchAndRenderBoxes();
                }

            } catch (err) {
                console.error('Erro na investigação OSINT de telefonia:', err);
                resultContainer.innerHTML = `<p style="color: var(--accent-red);"><i class="fa-solid fa-triangle-exclamation"></i> Erro ao processar consulta de telefonia OSINT.</p>`;
            }
        });
    }

    document.getElementById('closeInspectorModal')?.addEventListener('click', () => {
        document.getElementById('box3DInspectorModal')?.classList.remove('active');
    });

    async function triggerModalGeocode() {
        const input = document.getElementById('modalPlaceSearch');
        const query = input ? input.value.trim() : '';
        if (!query) {
            showToast('Digite uma cidade, endereço ou local para buscar.', 'warning');
            return;
        }

        showToast(`🔍 Buscando coordenadas para: "${query}"...`, 'info');

        try {
            let data = null;
            try {
                const res = await fetch(`/api/osint/geocode?query=${encodeURIComponent(query)}`);
                if (res.ok) data = await res.json();
            } catch (e) {}

            // Fallback direto via Nominatim OpenStreetMap se API local falhar
            if (!data || !data.success) {
                const nominatimRes = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`);
                const nomList = await nominatimRes.json();
                if (nomList && nomList.length > 0) {
                    data = {
                        success: true,
                        display_name: nomList[0].display_name,
                        lat: parseFloat(nomList[0].lat),
                        lon: parseFloat(nomList[0].lon)
                    };
                }
            }

            if (data && data.success) {
                const lat = data.lat;
                const lng = data.lon;

                document.getElementById('modalLat').value = lat;
                document.getElementById('modalLng').value = lng;

                if (selectedBox) {
                    selectedBox.latitude = lat;
                    selectedBox.longitude = lng;
                    selectedBox.has_gps = true;
                    selectedBox.is_inferred_gps = true;
                    selectedBox.address = {
                        success: true,
                        display_name: data.display_name
                    };
                    saveUploadToLocalStorage(selectedBox);
                    await fetchAndRenderBoxes();
                    openBox3DInspectorModal(selectedBox);
                }

                showToast(`📍 Coordenadas fixadas: ${lat.toFixed(4)}, ${lng.toFixed(4)} (${data.display_name.split(',')[0]})!`, 'success');
            } else {
                showToast('❌ Nenhum local encontrado para este termo.', 'error');
            }
        } catch (err) {
            console.error('Erro na geocodificação:', err);
            showToast('❌ Erro na consulta de endereço.', 'error');
        }
    }

    document.getElementById('btnGeocodeModal')?.addEventListener('click', triggerModalGeocode);
    document.getElementById('modalPlaceSearch')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            triggerModalGeocode();
        }
    });

    /* =========================================================================
       FERRAMENTAS DE INTELIGÊNCIA DE REDE & IP OSINT
       ========================================================================= */
    function setupNetworkOsintTools() {
        const btnLookup = document.getElementById('btnLookupIp');
        const ipInput = document.getElementById('ipTargetInput');
        const resultContainer = document.getElementById('ipResultContainer');

        if (!btnLookup || !ipInput || !resultContainer) return;

        btnLookup.addEventListener('click', async () => {
            const query = ipInput.value.trim();
            if (!query) {
                alert('Digite um endereço IP ou domínio válido para investigar.');
                return;
            }

            btnLookup.disabled = true;
            btnLookup.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Consultando...';

            try {
                const res = await fetch(`/api/osint/ip-lookup?target=${encodeURIComponent(query)}`);
                if (res.ok) {
                    const data = await res.json();
                    renderIpResults(data);
                } else {
                    resultContainer.innerHTML = `<div class="error-msg">Erro na consulta do IP/Domínio. Verifique o alvo informado.</div>`;
                }
            } catch (err) {
                console.error('Erro no IP Lookup:', err);
                resultContainer.innerHTML = `<div class="error-msg">Falha na conexão com a API de Geolocalização de IP.</div>`;
            } finally {
                btnLookup.disabled = false;
                btnLookup.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Investigar IP / Domínio';
            }
        });
    }

    function renderIpResults(data) {
        const container = document.getElementById('ipResultContainer');
        if (!container) return;

        if (data.status !== 'success') {
            container.innerHTML = `<div class="error-msg">Não foi possível geolocalizar o IP: ${data.message || 'Alvo inválido'}</div>`;
            return;
        }

        container.innerHTML = `
            <div class="ip-card glass-panel" style="margin-top: 14px; padding: 14px; border: 1px solid var(--accent-cyan); border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; font-size: 14px; color: var(--accent-cyan);">🌐 ${data.query} (${data.resolved_ip || data.query})</span>
                    <span style="font-size: 11px; background: rgba(6, 182, 212, 0.2); padding: 2px 8px; border-radius: 12px; color: #38bdf8;">${data.countryCode || 'N/A'}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; font-size: 12px;">
                    <div><strong>País:</strong> ${data.country || 'N/A'}</div>
                    <div><strong>Região/Estado:</strong> ${data.regionName || 'N/A'}</div>
                    <div><strong>Cidade:</strong> ${data.city || 'N/A'}</div>
                    <div><strong>Provedor (ISP):</strong> ${data.isp || 'N/A'}</div>
                    <div><strong>Organização:</strong> ${data.org || 'N/A'}</div>
                    <div><strong>AS / Rota:</strong> ${data.as || 'N/A'}</div>
                    <div><strong>Fuso Horário:</strong> ${data.timezone || 'N/A'}</div>
                    <div><strong>Coordenadas:</strong> ${data.lat}, ${data.lon}</div>
                </div>
                <div style="margin-top: 10px; display: flex; gap: 8px;">
                    <button onclick="window.onFocusCoords(${data.lat}, ${data.lon})" class="btn btn-sm btn-primary" style="flex: 1;">
                        <i class="fa-solid fa-map-pin"></i> Ver no Mapa
                    </button>
                    <a href="https://www.shodan.io/host/${data.query}" target="_blank" class="btn btn-sm btn-dark" style="text-align: center; text-decoration: none;">
                        <i class="fa-solid fa-satellite-dish"></i> Shodan OSINT
                    </a>
                </div>
            </div>
        `;
    }

    window.onFocusCoords = (lat, lon) => {
        focusOnLocation(lat, lon);
    };

    /* =========================================================================
       CALCULADORA GEODÉSICA DE DISTÂNCIA & VISADA
       ========================================================================= */
    function populateGeodesicDropdowns(boxes) {
        const selectA = document.getElementById('geoPointA');
        const selectB = document.getElementById('geoPointB');

        if (!selectA || !selectB) return;

        selectA.innerHTML = '';
        selectB.innerHTML = '';

        const withCoords = boxes.filter(b => b.latitude !== null && b.latitude !== undefined && b.longitude !== null && b.longitude !== undefined);

        if (withCoords.length === 0) {
            selectA.innerHTML = '<option value="">Nenhum alvo com GPS cadastrado</option>';
            selectB.innerHTML = '<option value="">Nenhum alvo com GPS cadastrado</option>';
            return;
        }

        withCoords.forEach((b, i) => {
            const title = `${b.code} - ${b.filename || b.title || 'Alvo'}`;
            const optA = document.createElement('option');
            optA.value = b.id;
            optA.innerText = title;
            if (i === 0) optA.selected = true;
            selectA.appendChild(optA);

            const optB = document.createElement('option');
            optB.value = b.id;
            optB.innerText = title;
            if (i === 1) optB.selected = true;
            selectB.appendChild(optB);
        });
    }

    function setupGeodesicCalculator() {
        document.getElementById('btnCalculateGeodesic')?.addEventListener('click', async () => {
            const idA = document.getElementById('geoPointA')?.value;
            const idB = document.getElementById('geoPointB')?.value;

            if (!idA || !idB || idA === idB) {
                alert('Selecione dois alvos diferentes para calcular a distância.');
                return;
            }

            const boxA = boxesData.find(b => b.id === idA);
            const boxB = boxesData.find(b => b.id === idB);

            if (!boxA || !boxB) return;

            try {
                const res = await fetch(`/api/osint/distance?lat1=${boxA.latitude}&lng1=${boxA.longitude}&lat2=${boxB.latitude}&lng2=${boxB.longitude}`);
                if (res.ok) {
                    const data = await res.json();
                    const resultBox = document.getElementById('geodesicResultBox');
                    if (resultBox) {
                        resultBox.style.display = 'grid';
                        resultBox.innerHTML = `
                            <div class="geodesic-metric">
                                <span class="geodesic-metric-val">${data.distance_meters} m</span>
                                <span class="geodesic-metric-lbl">Distância Direta (Metros)</span>
                            </div>
                            <div class="geodesic-metric">
                                <span class="geodesic-metric-val">${data.distance_km} km</span>
                                <span class="geodesic-metric-lbl">Distância em Quilômetros</span>
                            </div>
                            <div class="geodesic-metric">
                                <span class="geodesic-metric-val">${data.bearing_degrees}°</span>
                                <span class="geodesic-metric-lbl">Azimute de Visada (Bearing)</span>
                            </div>
                        `;
                    }
                }
            } catch (err) {
                console.error('Erro ao calcular distância geodésica:', err);
            }
        });
    }

    /* =========================================================================
       GERENCIAMENTO DE ABAS
       ========================================================================= */
    function setupTabSwitching() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                btn.classList.add('active');
                const targetTabId = btn.getAttribute('data-tab');
                document.getElementById(targetTabId)?.classList.add('active');

                if (targetTabId === 'tab2D' && map2D) {
                    setTimeout(() => map2D.invalidateSize(), 200);
                }
                if (targetTabId === 'tab3D' && engine3D) {
                    setTimeout(() => engine3D.onResize(), 200);
                }
            });
        });
    }

    /* =========================================================================
       UPLOAD DE FOTOS COM EXIF GPS
       ========================================================================= */
    function setupDropzone() {
        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('photoInput');

        if (!dropzone || !fileInput) return;

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                handlePhotoUpload(Array.from(e.dataTransfer.files));
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files.length > 0) {
                const files = Array.from(fileInput.files);
                fileInput.value = '';
                handlePhotoUpload(files);
            }
        });
    }

    async function handlePhotoUpload(files) {
        const dropzone = document.getElementById('dropzone');
        dropzone?.classList.add('processing');

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            showToast(`🔬 Processando arquivo: ${file.name}...`, 'info');

            let clientLat = null;
            let clientLng = null;
            let clientAlt = null;
            let clientCamera = 'Não informada';
            let clientSoftware = null;
            let clientDate = new Date().toLocaleString();
            let thumbnailBase64 = null;
            let sha256Hash = null;

            // 1. Calcular Hash SHA-256 no Navegador via Web Crypto
            try {
                const arrayBuffer = await file.arrayBuffer();
                const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                sha256Hash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            } catch (e) {
                console.warn('Erro ao gerar SHA-256 no cliente:', e);
            }

            // 2. Gerar Thumbnail DataURL no Navegador
            if (file.type.startsWith('image/')) {
                try {
                    thumbnailBase64 = await new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onload = (e) => resolve(e.target.result);
                        reader.readAsDataURL(file);
                    });
                } catch (e) {}
            }

            // 3. Extração Client-Side Instantânea de Metadados EXIF/GPS (exifr)
            if (window.exifr && file.type.startsWith('image/')) {
                try {
                    const gpsData = await window.exifr.gps(file).catch(() => null);
                    if (gpsData && gpsData.latitude !== undefined && gpsData.longitude !== undefined) {
                        clientLat = Number(gpsData.latitude);
                        clientLng = Number(gpsData.longitude);
                        clientAlt = Number(gpsData.altitude || 0);
                    }
                    const exifData = await window.exifr.parse(file).catch(() => null);
                    if (exifData) {
                        if (clientLat === null && exifData.latitude !== undefined && exifData.longitude !== undefined) {
                            clientLat = Number(exifData.latitude);
                            clientLng = Number(exifData.longitude);
                            clientAlt = Number(exifData.altitude || 0);
                        }
                        if (exifData.Make || exifData.Model) {
                            clientCamera = `${exifData.Make || ''} ${exifData.Model || ''}`.trim();
                        }
                        if (exifData.Software) {
                            clientSoftware = exifData.Software;
                        }
                        if (exifData.DateTimeOriginal) {
                            clientDate = new Date(exifData.DateTimeOriginal).toLocaleString();
                        }
                    }
                } catch (err) {
                    console.warn('Leitura EXIF local:', err);
                }
            }

            const uniqueId = 'local_' + Math.random().toString(36).substr(2, 9);
            const nextCode = `GEO-${String(boxesData.length + 1).padStart(3, '0')}`;

            const localBox = {
                id: uniqueId,
                code: nextCode,
                title: file.name,
                filename: file.name,
                notes: 'Arquivo analisado via plataforma GEONIV OSINT.',
                photo_url: thumbnailBase64 || '',
                photo_thumbnail: thumbnailBase64,
                latitude: clientLat,
                longitude: clientLng,
                altitude: clientAlt,
                has_gps: clientLat !== null && clientLng !== null,
                camera_info: clientCamera,
                date_added: clientDate,
                software: clientSoftware,
                category: file.type.startsWith('image/') ? 'image' : (file.name.endsWith('.pdf') ? 'pdf' : 'document'),
                hashes: { sha256: sha256Hash },
                scrubbing_analysis: {
                    scrubbing_detected: clientLat === null && file.type.startsWith('image/'),
                    scrubbing_source: file.name.includes('WA') ? 'WhatsApp / Mensageiro' : 'Compressão / Web',
                    explanation: clientLat === null ? 'Esta imagem não contém coordenadas de satélite no EXIF (comum em fotos baixadas da web ou recebidas por redes sociais).' : ''
                }
            };

            // Geocodificação reversa client-side se GPS presente
            if (clientLat !== null && clientLng !== null) {
                try {
                    const nomRes = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${clientLat}&lon=${clientLng}&format=json`).catch(() => null);
                    if (nomRes && nomRes.ok) {
                        const nomData = await nomRes.json();
                        localBox.address = {
                            success: true,
                            display_name: nomData.display_name,
                            road: nomData.address?.road,
                            suburb: nomData.address?.suburb || nomData.address?.neighbourhood,
                            city: nomData.address?.city || nomData.address?.town,
                            state: nomData.address?.state,
                            country: nomData.address?.country,
                            postcode: nomData.address?.postcode
                        };
                    }
                } catch (e) {}
            }

            // Salva instantaneamente no localStorage e atualiza estado
            saveUploadToLocalStorage(localBox);
            await fetchAndRenderBoxes();

            if (clientLat !== null && clientLng !== null) {
                showToast(`📍 GPS detectado: ${clientLat.toFixed(4)}, ${clientLng.toFixed(4)} (${clientCamera})`, 'success');
                focusOnLocation(clientLat, clientLng);
            } else {
                showToast(`⚠️ Imagem sem GPS EXIF. Use o buscador de cidades ou os botões de busca por IA!`, 'warning');
            }

            setTimeout(() => openBox3DInspectorModal(localBox), 200);

            // 4. Sincronização em Segundo Plano com o Backend
            const formData = new FormData();
            formData.append('file', file);
            formData.append('notes', 'Foto analisada via plataforma GEONIV OSINT.');

            fetch('/api/upload', {
                method: 'POST',
                body: formData
            }).then(async (res) => {
                if (res.ok) {
                    const serverBox = await res.json();
                    if (serverBox && serverBox.latitude !== null) {
                        localBox.latitude = serverBox.latitude;
                        localBox.longitude = serverBox.longitude;
                        localBox.altitude = serverBox.altitude;
                        localBox.has_gps = true;
                        localBox.address = serverBox.address;
                        saveUploadToLocalStorage(localBox);
                        await fetchAndRenderBoxes();
                    }
                }
            }).catch((err) => {
                console.warn('Sync com servidor backend opcional:', err);
            });
        }

        dropzone?.classList.remove('processing');
    }

    /* =========================================================================
       FORMULÁRIO DE MANUTENÇÃO & BUSCA
       ========================================================================= */
    function setupFormEvents() {
        const form = document.getElementById('boxForm');
        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const boxId = document.getElementById('modalBoxId').value;
            if (!boxId) return;

            const latVal = document.getElementById('modalLat').value;
            const lngVal = document.getElementById('modalLng').value;
            const altVal = document.getElementById('modalAltitude').value;

            const payload = {
                code: document.getElementById('modalCode').value,
                title: document.getElementById('modalTitle').value,
                altitude: altVal !== '' ? parseFloat(altVal) : null,
                latitude: latVal !== '' ? parseFloat(latVal) : null,
                longitude: lngVal !== '' ? parseFloat(lngVal) : null,
                notes: document.getElementById('modalNotes').value
            };

            try {
                const res = await fetch(`/api/boxes/${boxId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    const updated = await res.json();
                    saveUploadToLocalStorage(updated);

                    document.getElementById('box3DInspectorModal')?.classList.remove('active');
                    await fetchAndRenderBoxes();
                }
            } catch (err) {
                console.error('Erro ao salvar registro:', err);
            }
        });

        document.getElementById('btnDeleteBox')?.addEventListener('click', async () => {
            const boxId = document.getElementById('modalBoxId').value;
            if (!boxId || !confirm('Deseja realmente remover este alvo?')) return;

            try {
                const res = await fetch(`/api/boxes/${boxId}`, { method: 'DELETE' });
                if (res.ok) {
                    document.getElementById('box3DInspectorModal')?.classList.remove('active');
                    await fetchAndRenderBoxes();
                }
            } catch (err) {
                console.error('Erro ao excluir registro:', err);
            }
        });

        document.getElementById('btnManualAdd')?.addEventListener('click', async () => {
            const defaultCode = `GEO-${String(boxesData.length + 1).padStart(3, '0')}`;
            const newBoxPayload = {
                code: defaultCode,
                title: 'Novo Alvo GEOINT',
                latitude: -23.55052,
                longitude: -46.633308,
                altitude: 760.0,
                notes: 'Novo ponto de inteligência cadastrado.'
            };

            try {
                const res = await fetch('/api/boxes/manual', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newBoxPayload)
                });
                if (res.ok) {
                    const createdBox = await res.json();
                    saveUploadToLocalStorage(createdBox);

                    await fetchAndRenderBoxes();
                    openBox3DInspectorModal(createdBox);
                }
            } catch (err) {
                console.error('Erro ao cadastrar registro manual:', err);
            }
        });
    }

    function setupSearchFilter() {
        const searchInput = document.getElementById('searchInput');
        searchInput?.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            saveSearchToLocalStorage(query);

            const filtered = boxesData.filter(b => 
                (b.code && b.code.toLowerCase().includes(query)) ||
                (b.filename && b.filename.toLowerCase().includes(query)) ||
                (b.title && b.title.toLowerCase().includes(query)) ||
                (b.camera_info && b.camera_info.toLowerCase().includes(query)) ||
                (b.notes && b.notes.toLowerCase().includes(query))
            );
            renderBoxesList(filtered);
        });
    }

    /* =========================================================================
       CENTRAL DE FERRAMENTAS & DIRETÓRIO OSINT HUB (FILTROS E BUSCA)
       ========================================================================= */
    function setupOsintHub() {
        const filterBtns = document.querySelectorAll('.osint-filter-btn');
        const searchInput = document.getElementById('osintHubSearchInput');
        const toolCards = document.querySelectorAll('.osint-tool-card');

        let activeCategory = 'all';
        let searchQuery = '';

        function applyOsintFilter() {
            toolCards.forEach(card => {
                const cardCategory = card.getAttribute('data-category');
                const cardText = card.innerText.toLowerCase();

                const matchesCategory = (activeCategory === 'all' || cardCategory === activeCategory);
                const matchesSearch = (!searchQuery || cardText.includes(searchQuery));

                if (matchesCategory && matchesSearch) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                activeCategory = btn.getAttribute('data-category') || 'all';
                applyOsintFilter();
            });
        });

        searchInput?.addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            applyOsintFilter();
        });
    }
});
