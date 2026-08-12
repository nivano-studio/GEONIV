/**
 * GEONIV 3D - Motor de Visualização 3D Tecnológica & Digital Twin
 * Desenvolvido com Three.js (WebGL)
 */

class Geoniv3DEngine {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;

        // Animações e Objetos
        this.nodesGroup = new THREE.Group();
        this.terrainMesh = null;

        // Estado do Inspetor 3D
        this.inspectorScene = null;
        this.inspectorCamera = null;
        this.inspectorRenderer = null;
        this.inspectorControls = null;
        this.inspectorNodeGroup = null;
        this.explodedLayers = [];

        this.initTerrainScene();
    }

    /* =========================================================================
       1. CENÁRIO 3D PRINCIPAL (TERRENO TECNOLÓGICO)
       ========================================================================= */
    initTerrainScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x070b14);
        this.scene.fog = new THREE.FogExp2(0x070b14, 0.015);

        const width = this.container.clientWidth || window.innerWidth;
        const height = this.container.clientHeight || 600;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(0, 16, 28);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;

        this.container.appendChild(this.renderer.domElement);

        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxPolarAngle = Math.PI / 2 - 0.02;
        this.controls.minDistance = 3;
        this.controls.maxDistance = 120;

        // Iluminação Futurista Cyan/Green
        const ambientLight = new THREE.AmbientLight(0xe0f2fe, 0.7);
        this.scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xffffff, 1.2);
        sunLight.position.set(30, 40, 20);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 2048;
        sunLight.shadow.mapSize.height = 2048;
        this.scene.add(sunLight);

        const pointLight = new THREE.PointLight(0x06b6d4, 1.5, 60);
        pointLight.position.set(0, 12, 0);
        this.scene.add(pointLight);

        this.createTerrain();
        this.scene.add(this.nodesGroup);

        window.addEventListener('resize', () => this.onResize());
        this.setupRaycaster();
        this.animate();
    }

    createTerrain() {
        const terrainGeo = new THREE.PlaneGeometry(100, 100, 40, 40);
        const pos = terrainGeo.attributes.position;
        for (let i = 0; i < pos.count; i++) {
            const vx = pos.getX(i);
            const vy = pos.getY(i);
            const z = Math.sin(vx * 0.08) * Math.cos(vy * 0.08) * 0.6;
            pos.setZ(i, z);
        }
        terrainGeo.computeVertexNormals();

        const terrainMat = new THREE.MeshStandardMaterial({
            color: 0x0b1329,
            roughness: 0.7,
            metalness: 0.2,
            flatShading: true
        });

        this.terrainMesh = new THREE.Mesh(terrainGeo, terrainMat);
        this.terrainMesh.rotation.x = -Math.PI / 2;
        this.terrainMesh.receiveShadow = true;
        this.scene.add(this.terrainMesh);

        const gridHelper = new THREE.GridHelper(100, 50, 0x06b6d4, 0x1e293b);
        gridHelper.position.y = 0.05;
        this.scene.add(gridHelper);
    }

    /* =========================================================================
       2. GERAÇÃO DO MODELO 3D TECNOLÓGICO (GEO-SCANNER NODE)
       ========================================================================= */
    createGeoScannerModel(itemData, isForInspector = false) {
        const nodeGroup = new THREE.Group();
        nodeGroup.userData = { itemData: itemData, isNode: true };

        const metalMat = new THREE.MeshStandardMaterial({
            color: 0x1e293b,
            metalness: 0.9,
            roughness: 0.2
        });

        const cyanGlowMat = new THREE.MeshStandardMaterial({
            color: 0x06b6d4,
            emissive: 0x06b6d4,
            emissiveIntensity: 1.2,
            roughness: 0.1
        });

        const emeraldGlowMat = new THREE.MeshStandardMaterial({
            color: 0x10b981,
            emissive: 0x10b981,
            emissiveIntensity: 1.2,
            roughness: 0.1
        });

        const glassMat = new THREE.MeshPhysicalMaterial({
            color: 0x38bdf8,
            transmission: 0.8,
            transparent: true,
            opacity: 0.9,
            roughness: 0.1
        });

        const layers = [];
        let currentY = isForInspector ? 0 : 0.5;

        // 1. Base do Scanner
        const baseGroup = new THREE.Group();
        const baseGeo = new THREE.CylinderGeometry(1.2, 1.4, 0.4, 16);
        const baseMesh = new THREE.Mesh(baseGeo, metalMat);
        baseMesh.position.y = 0.2;
        baseMesh.castShadow = true;
        baseGroup.add(baseMesh);

        // Anel de luz LED na base
        const ringGeo = new THREE.TorusGeometry(1.25, 0.05, 8, 32);
        const ringMesh = new THREE.Mesh(ringGeo, cyanGlowMat);
        ringMesh.rotation.x = Math.PI / 2;
        ringMesh.position.y = 0.25;
        baseGroup.add(ringMesh);

        baseGroup.position.y = currentY;
        nodeGroup.add(baseGroup);
        layers.push({ name: "Base do Scanner", group: baseGroup, defaultY: currentY });
        currentY += 0.5;

        // 2. Núcleo Óptico de Geolocalização
        const coreGroup = new THREE.Group();
        const coreGeo = new THREE.CylinderGeometry(0.9, 0.9, 0.8, 16);
        const coreMesh = new THREE.Mesh(coreGeo, metalMat);
        coreMesh.position.y = 0.4;
        coreMesh.castShadow = true;
        coreGroup.add(coreMesh);

        // Lente central brilhante
        const lensGeo = new THREE.SphereGeometry(0.4, 16, 16);
        const lensMesh = new THREE.Mesh(lensGeo, glassMat);
        lensMesh.position.set(0, 0.4, 0.7);
        coreGroup.add(lensMesh);

        coreGroup.position.y = currentY;
        nodeGroup.add(coreGroup);
        layers.push({ name: "Núcleo de Câmera & EXIF", group: coreGroup, defaultY: currentY });
        currentY += 0.9;

        // 3. Cúpula Sensor Aérea
        const domeGroup = new THREE.Group();
        const domeGeo = new THREE.SphereGeometry(0.8, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2);
        const domeMesh = new THREE.Mesh(domeGeo, metalMat);
        domeMesh.position.y = 0.1;
        domeMesh.castShadow = true;
        domeGroup.add(domeMesh);

        // Antena GPS no topo
        const antennaGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.6, 8);
        const antennaMesh = new THREE.Mesh(antennaGeo, emeraldGlowMat);
        antennaMesh.position.y = 0.9;
        domeGroup.add(antennaMesh);

        domeGroup.position.y = currentY;
        nodeGroup.add(domeGroup);
        layers.push({ name: "Antena GPS & Sensor EXIF", group: domeGroup, defaultY: currentY });

        // Placa 3D com Nome do Arquivo
        const labelCanvas = document.createElement('canvas');
        labelCanvas.width = 256;
        labelCanvas.height = 128;
        const ctx = labelCanvas.getContext('2d');
        ctx.fillStyle = '#06b6d4';
        ctx.fillRect(0, 0, 256, 128);
        ctx.fillStyle = '#070b14';
        ctx.font = 'bold 36px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(itemData.code || 'GEO-3D', 128, 64);

        const badgeTex = new THREE.CanvasTexture(labelCanvas);
        const badgeGeo = new THREE.PlaneGeometry(0.8, 0.4);
        const badgeMat = new THREE.MeshBasicMaterial({ map: badgeTex, side: THREE.DoubleSide });
        const badgeMesh = new THREE.Mesh(badgeGeo, badgeMat);
        badgeMesh.position.set(0, currentY + 0.5, 0);
        nodeGroup.add(badgeMesh);

        if (isForInspector) {
            this.explodedLayers = layers;
        }

        return nodeGroup;
    }

    /* =========================================================================
       3. POSICIONAR ITENS NO DIGITAL TWIN
       ========================================================================= */
    renderBoxesIn3DTerrain(items) {
        while (this.nodesGroup.children.length > 0) {
            const obj = this.nodesGroup.children[0];
            this.nodesGroup.remove(obj);
        }

        if (!items || items.length === 0) return;

        let centerLat = 0;
        let centerLng = 0;
        let validGpsCount = 0;

        items.forEach(b => {
            if (b.latitude && b.longitude) {
                centerLat += b.latitude;
                centerLng += b.longitude;
                validGpsCount++;
            }
        });

        if (validGpsCount === 0) {
            centerLat = -23.55052;
            centerLng = -46.633308;
        } else {
            centerLat /= validGpsCount;
            centerLng /= validGpsCount;
        }

        const scaleFactor = 12000;

        items.forEach((item, index) => {
            const nodeMesh = this.createGeoScannerModel(item, false);

            let posX = 0;
            let posZ = 0;

            if (item.latitude && item.longitude) {
                posX = (item.longitude - centerLng) * scaleFactor;
                posZ = (item.latitude - centerLat) * scaleFactor;
            } else {
                const angle = index * 1.5;
                const radius = 6 + index * 4;
                posX = Math.cos(angle) * radius;
                posZ = Math.sin(angle) * radius;
            }

            nodeMesh.position.set(posX, 0, posZ);
            this.nodesGroup.add(nodeMesh);
        });

        this.controls.target.set(0, 1, 0);
    }

    /* =========================================================================
       4. INSPETOR 3D INDIVIDUAL
       ========================================================================= */
    openHive3DInspector(itemData) {
        const container = document.getElementById('inspector3DCanvas');
        if (!container) return;

        container.innerHTML = '';

        this.inspectorScene = new THREE.Scene();
        this.inspectorScene.background = new THREE.Color(0x070b14);

        const w = container.clientWidth || 500;
        const h = container.clientHeight || 450;

        this.inspectorCamera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100);
        this.inspectorCamera.position.set(4, 4, 6);

        this.inspectorRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.inspectorRenderer.setSize(w, h);
        this.inspectorRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        container.appendChild(this.inspectorRenderer.domElement);

        this.inspectorControls = new THREE.OrbitControls(this.inspectorCamera, this.inspectorRenderer.domElement);
        this.inspectorControls.enableDamping = true;
        this.inspectorControls.autoRotate = true;
        this.inspectorControls.autoRotateSpeed = 1.0;

        const ambient = new THREE.AmbientLight(0xffffff, 0.8);
        this.inspectorScene.add(ambient);

        const dirLight = new THREE.DirectionalLight(0x06b6d4, 1.5);
        dirLight.position.set(10, 15, 10);
        this.inspectorScene.add(dirLight);

        const circleGridGeo = new THREE.CircleGeometry(3, 32);
        const circleGridMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, wireframe: true, transparent: true, opacity: 0.2 });
        const circleGrid = new THREE.Mesh(circleGridGeo, circleGridMat);
        circleGrid.rotation.x = -Math.PI / 2;
        this.inspectorScene.add(circleGrid);

        this.inspectorNodeGroup = this.createGeoScannerModel(itemData, true);
        this.inspectorScene.add(this.inspectorNodeGroup);

        const renderInspector = () => {
            if (!this.inspectorScene) return;
            requestAnimationFrame(renderInspector);
            this.inspectorControls.update();
            this.inspectorRenderer.render(this.inspectorScene, this.inspectorCamera);
        };
        renderInspector();
    }

    setExplosionFactor(factor) {
        if (!this.explodedLayers || this.explodedLayers.length === 0) return;
        this.explodedLayers.forEach((layer, index) => {
            const targetY = layer.defaultY + index * factor * 1.0;
            layer.group.position.y = THREE.MathUtils.lerp(layer.group.position.y, targetY, 0.2);
        });
    }

    /* =========================================================================
       5. RAYCASTING DE CLIQUE (ESQUERDO E DIREITO)
       ========================================================================= */
    setupRaycaster() {
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        let startX = 0;
        let startY = 0;

        this.renderer.domElement.addEventListener('pointerdown', (e) => {
            startX = e.clientX;
            startY = e.clientY;
        });

        this.renderer.domElement.addEventListener('pointerup', (e) => {
            // Verificar se foi um clique estático e não um arrasto de rotação da câmera (distância < 6px)
            const dist = Math.hypot(e.clientX - startX, e.clientY - startY);
            if (dist > 6) return;

            const rect = this.renderer.domElement.getBoundingClientRect();
            this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

            this.raycaster.setFromCamera(this.mouse, this.camera);
            const intersects = this.raycaster.intersectObjects(this.nodesGroup.children, true);

            if (intersects.length > 0) {
                let obj = intersects[0].object;
                while (obj && !obj.userData.isNode) {
                    obj = obj.parent;
                }

                if (obj && obj.userData && obj.userData.itemData) {
                    if (window.onSelectBoxFrom3D) {
                        window.onSelectBoxFrom3D(obj.userData.itemData);
                    }
                }
            }
        });
    }

    animate() {
        requestAnimationFrame((t) => this.animate(t));
        if (this.controls) this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    onResize() {
        if (!this.container || !this.renderer || !this.camera) return;
        const w = this.container.clientWidth;
        const h = this.container.clientHeight || 600;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    }
}

window.Geoniv3DEngine = Geoniv3DEngine;
