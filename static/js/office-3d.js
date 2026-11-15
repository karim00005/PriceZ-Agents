/**
 * PriceZ Agents - Real Interactive 3D AI Virtual Office
 * High Performance WebGL 3D Office Simulation with Three.js
 */

(function (window) {
  'use strict';

  // =========================================================================
  // 1. CONSTANTS & CONFIGURATION
  // =========================================================================
  const CONFIG = {
    floorWidth: 34,
    floorDepth: 26,
    wallHeight: 7.5,
    colors: {
      navyBg: 0x070b14,
      floorWood: 0x1a2233,
      deskWood: 0x223048,
      deskLegs: 0x0f172a,
      glassWall: 0x38bdf8,
      wallDark: 0x0b1322,
      wallAccent: 0x111c33,
      cyanGlow: 0x00f2fe,
      blueGlow: 0x2563eb,
      purpleGlow: 0x8b5cf6,
      emeraldGlow: 0x10b981,
      amberGlow: 0xf59e0b,
      roseGlow: 0xf43f5e
    },
    cameraPresets: {
      overview: { pos: { x: 0, y: 19, z: 22 }, target: { x: 0, y: 1.5, z: 0 } },
      sales: { pos: { x: -6, y: 4.5, z: 7 }, target: { x: -7, y: 1.2, z: 2 } },
      report: { pos: { x: -6, y: 4.5, z: 11 }, target: { x: -7, y: 1.2, z: 6 } },
      support: { pos: { x: 1, y: 4.5, z: 10 }, target: { x: 1, y: 1.2, z: 5 } },
      content: { pos: { x: 8, y: 4.5, z: 10 }, target: { x: 8, y: 1.2, z: 5 } },
      research: { pos: { x: 8, y: 4.5, z: 6 }, target: { x: 8, y: 1.2, z: 1 } },
      architect: { pos: { x: -1, y: 4.5, z: -1 }, target: { x: -1, y: 1.5, z: -6 } },
      coffee: { pos: { x: 10, y: 5.5, z: -1 }, target: { x: 11.5, y: 1.5, z: -6 } },
      meeting: { pos: { x: -6, y: 5.5, z: -1 }, target: { x: -7, y: 1.5, z: -6 } }
    }
  };

  // Waypoints for obstacle-free office walking
  const WAYPOINTS = {
    // Corridors
    c_center: { x: 0, z: 1 },
    c_north: { x: 0, z: -4 },
    c_south: { x: 0, z: 7 },
    c_east: { x: 5, z: 1 },
    c_west: { x: -4, z: 1 },
    // Destinations
    coffee_bar: { x: 10.5, z: -6 },
    water_cooler: { x: 12.5, z: -4 },
    lounge_sofa: { x: 5, z: -5.5 },
    panoramic_window: { x: 13.5, z: 2 },
    meeting_table: { x: -6.5, z: -5 },
    server_rack: { x: -2, z: -7.5 },
    // Desk Chairs
    chair_sales: { x: -7, z: 3.2 },
    chair_report: { x: -7, z: 7.2 },
    chair_support: { x: 1, z: 6.2 },
    chair_content: { x: 8, z: 6.2 },
    chair_research: { x: 8, z: 2.2 },
    chair_architect: { x: -1, z: -4.8 }
  };

  // Waypoint Graph Connections for routing
  const WAYPOINT_GRAPH = {
    c_center: ['c_north', 'c_south', 'c_east', 'c_west'],
    c_north: ['c_center', 'lounge_sofa', 'coffee_bar', 'meeting_table', 'server_rack', 'chair_architect'],
    c_south: ['c_center', 'chair_support'],
    c_east: ['c_center', 'chair_research', 'chair_content', 'panoramic_window', 'water_cooler'],
    c_west: ['c_center', 'chair_sales', 'chair_report'],
    coffee_bar: ['c_north', 'water_cooler'],
    water_cooler: ['c_east', 'coffee_bar'],
    lounge_sofa: ['c_north'],
    panoramic_window: ['c_east'],
    meeting_table: ['c_north'],
    server_rack: ['c_north'],
    chair_sales: ['c_west'],
    chair_report: ['c_west'],
    chair_support: ['c_south'],
    chair_content: ['c_east'],
    chair_research: ['c_east'],
    chair_architect: ['c_north']
  };

  // =========================================================================
  // 2. OFFICE 3D CORE ENGINE
  // =========================================================================
  class Office3DEngine {
    constructor(containerId) {
      this.container = document.getElementById(containerId);
      if (!this.container) {
        console.error('[Office3D] Container not found:', containerId);
        return;
      }

      this.scene = null;
      this.camera = null;
      this.renderer = null;
      this.controls = null;
      this.clock = new THREE.Clock();

      this.agents = new Map();
      this.workstations = new Map();
      this.clickableObjects = [];
      this.animatedMonitors = [];
      this.interactiveProps = [];

      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();
      this.hoveredObject = null;
      this.selectedAgentId = null;

      this.initScene();
      this.initLighting();
      this.initEnvironment();
      this.initWorkstations();
      this.initCharacters();
      this.initInteraction();
      this.animate();

      window.addEventListener('resize', () => this.onWindowResize());
    }

    // -----------------------------------------------------------------------
    // Scene & Renderer Setup
    // -----------------------------------------------------------------------
    initScene() {
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(CONFIG.colors.navyBg);
      this.scene.fog = new THREE.FogExp2(CONFIG.colors.navyBg, 0.015);

      const width = this.container.clientWidth;
      const height = this.container.clientHeight;

      this.camera = new THREE.PerspectiveCamera(40, width / height, 0.5, 150);
      this.camera.position.set(CONFIG.cameraPresets.overview.pos.x, CONFIG.cameraPresets.overview.pos.y, CONFIG.cameraPresets.overview.pos.z);

      this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.shadowMap.enabled = true;
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.15;

      this.container.appendChild(this.renderer.domElement);

      // OrbitControls
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.06;
      this.controls.maxPolarAngle = Math.PI / 2.08; // Prevent looking below floor
      this.controls.minDistance = 4;
      this.controls.maxDistance = 45;
      this.controls.target.set(0, 1.5, 0);
    }

    // -----------------------------------------------------------------------
    // Lighting
    // -----------------------------------------------------------------------
    initLighting() {
      // Ambient Light
      const ambient = new THREE.AmbientLight(0x182642, 1.8);
      this.scene.add(ambient);

      // Key Sunlight / Window Directional Light
      const dirLight = new THREE.DirectionalLight(0xdbeafe, 1.4);
      dirLight.position.set(18, 24, 14);
      dirLight.castShadow = true;
      dirLight.shadow.mapSize.width = 2048;
      dirLight.shadow.mapSize.height = 2048;
      dirLight.shadow.camera.near = 1;
      dirLight.shadow.camera.far = 60;
      dirLight.shadow.camera.left = -20;
      dirLight.shadow.camera.right = 20;
      dirLight.shadow.camera.top = 20;
      dirLight.shadow.camera.bottom = -20;
      dirLight.shadow.bias = -0.0005;
      this.scene.add(dirLight);

      // Ceiling Architectural Spotlights
      const spotLocations = [
        { x: -7, y: 7, z: 2, color: 0x38bdf8 },
        { x: -7, y: 7, z: 6, color: 0x818cf8 },
        { x: 1, y: 7, z: 5, color: 0x38bdf8 },
        { x: 8, y: 7, z: 5, color: 0xc084fc },
        { x: 8, y: 7, z: 1, color: 0x34d399 },
        { x: -1, y: 7, z: -6, color: 0x22d3ee },
        { x: 11, y: 7, z: -6, color: 0xfbbf24 },
        { x: -7, y: 7, z: -6, color: 0x60a5fa }
      ];

      spotLocations.forEach(loc => {
        const spot = new THREE.SpotLight(loc.color, 1.2, 16, Math.PI / 4, 0.4, 1.5);
        spot.position.set(loc.x, loc.y, loc.z);
        spot.target.position.set(loc.x, 0, loc.z);
        this.scene.add(spot);
        this.scene.add(spot.target);

        // Ceiling Light Fixture Mesh
        const fixture = new THREE.Mesh(
          new THREE.CylinderGeometry(0.3, 0.35, 0.15, 16),
          new THREE.MeshStandardMaterial({ color: 0x0f172a, emissive: loc.color, emissiveIntensity: 0.6 })
        );
        fixture.position.set(loc.x, loc.y, loc.z);
        this.scene.add(fixture);
      });

      // Neon Backlight for PriceZ Logo
      const logoLight = new THREE.PointLight(CONFIG.colors.cyanGlow, 2.0, 10);
      logoLight.position.set(0, 4.5, -11.5);
      this.scene.add(logoLight);
    }

    // -----------------------------------------------------------------------
    // 3D Office Environment & Architecture
    // -----------------------------------------------------------------------
    initEnvironment() {
      const officeGroup = new THREE.Group();

      // 1. Wood Parquet Floor with Procedural Canvas Texture
      const floorCanvas = document.createElement('canvas');
      floorCanvas.width = 1024;
      floorCanvas.height = 1024;
      const fCtx = floorCanvas.getContext('2d');
      fCtx.fillStyle = '#101726';
      fCtx.fillRect(0, 0, 1024, 1024);

      // Draw wood parquet planks
      fCtx.strokeStyle = 'rgba(30, 41, 59, 0.8)';
      fCtx.lineWidth = 4;
      for (let y = 0; y < 1024; y += 64) {
        fCtx.beginPath();
        fCtx.moveTo(0, y);
        fCtx.lineTo(1024, y);
        fCtx.stroke();
      }
      for (let x = 0; x < 1024; x += 128) {
        for (let y = 0; y < 1024; y += 64) {
          fCtx.beginPath();
          fCtx.moveTo(x + (y % 128 === 0 ? 0 : 64), y);
          fCtx.lineTo(x + (y % 128 === 0 ? 0 : 64), y + 64);
          fCtx.stroke();
        }
      }

      const floorTex = new THREE.CanvasTexture(floorCanvas);
      floorTex.wrapS = THREE.RepeatWrapping;
      floorTex.wrapT = THREE.RepeatWrapping;
      floorTex.repeat.set(6, 5);

      const floorMat = new THREE.MeshStandardMaterial({
        map: floorTex,
        roughness: 0.4,
        metalness: 0.15
      });
      const floor = new THREE.Mesh(new THREE.PlaneGeometry(CONFIG.floorWidth, CONFIG.floorDepth), floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.receiveShadow = true;
      officeGroup.add(floor);

      // 2. Main Back Wall (Z = -CONFIG.floorDepth / 2)
      const wallMat = new THREE.MeshStandardMaterial({ color: CONFIG.colors.wallDark, roughness: 0.8 });
      const backWall = new THREE.Mesh(new THREE.BoxGeometry(CONFIG.floorWidth, CONFIG.wallHeight, 0.6), wallMat);
      backWall.position.set(0, CONFIG.wallHeight / 2, -CONFIG.floorDepth / 2);
      backWall.receiveShadow = true;
      officeGroup.add(backWall);

      // Accent wall panel behind main branding
      const accentMat = new THREE.MeshStandardMaterial({
        color: 0x162238,
        roughness: 0.5,
        metalness: 0.3
      });
      const accentPanel = new THREE.Mesh(new THREE.BoxGeometry(16, 5, 0.2), accentMat);
      accentPanel.position.set(0, 4.2, -CONFIG.floorDepth / 2 + 0.35);
      officeGroup.add(accentPanel);

      // 3. Illuminated 3D Branding Wall: "PriceZ Agents"
      this.createBrandingWall(officeGroup);

      // 4. West Left Wall with Modern Panels
      const leftWall = new THREE.Mesh(new THREE.BoxGeometry(0.6, CONFIG.wallHeight, CONFIG.floorDepth), wallMat);
      leftWall.position.set(-CONFIG.floorWidth / 2, CONFIG.wallHeight / 2, 0);
      leftWall.receiveShadow = true;
      officeGroup.add(leftWall);

      // 5. Panoramic Floor-to-Ceiling Windows & Modern Cityscape View (East Wall)
      this.createPanoramicWindowsAndSkyline(officeGroup);

      // 6. Glass Meeting Room (Partition with Glass Walls & Door)
      this.createMeetingRoom(officeGroup);

      // 7. Server Room Partition with Glowing Blinking Servers
      this.createServerRoom(officeGroup);

      // 8. Lounge & Collaboration Area (Sofa, Coffee Table, Plant Decor)
      this.createLoungeArea(officeGroup);

      // 9. Modern Coffee Corner & Break Bar
      this.createCoffeeBar(officeGroup);

      // 10. Plants & Greenery
      this.createOfficePlants(officeGroup);

      this.scene.add(officeGroup);
    }

    // -----------------------------------------------------------------------
    // 3D Branding Wall Sign
    // -----------------------------------------------------------------------
    createBrandingWall(parent) {
      const brandCanvas = document.createElement('canvas');
      brandCanvas.width = 1024;
      brandCanvas.height = 256;
      const ctx = brandCanvas.getContext('2d');

      // Draw Glowing Net Agent / PriceZ Agents Logo
      ctx.fillStyle = '#111a2e';
      ctx.fillRect(0, 0, 1024, 256);

      // Glowing border
      ctx.strokeStyle = '#00f2fe';
      ctx.lineWidth = 8;
      ctx.strokeRect(10, 10, 1004, 236);

      // Crown & Text
      ctx.font = 'bold 75px Cairo, sans-serif';
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      ctx.shadowColor = '#00f2fe';
      ctx.shadowBlur = 30;
      ctx.fillText('👑 PriceZ Agents', 512, 115);

      ctx.font = 'bold 36px Cairo, sans-serif';
      ctx.fillStyle = '#38bdf8';
      ctx.shadowBlur = 15;
      ctx.fillText('AI AGENTS VIRTUAL OFFICE • AUTONOMOUS STUDIO', 512, 185);

      const brandTex = new THREE.CanvasTexture(brandCanvas);
      const signMat = new THREE.MeshStandardMaterial({
        map: brandTex,
        roughness: 0.2,
        metalness: 0.8,
        emissive: 0x00f2fe,
        emissiveIntensity: 0.25
      });
      const brandSign = new THREE.Mesh(new THREE.BoxGeometry(10, 2.5, 0.15), signMat);
      brandSign.position.set(0, 4.4, -CONFIG.floorDepth / 2 + 0.55);
      parent.add(brandSign);
    }

    // -----------------------------------------------------------------------
    // Panoramic Windows & 3D Procedural Night City Skyline
    // -----------------------------------------------------------------------
    createPanoramicWindowsAndSkyline(parent) {
      // Window Frame Pillars
      const frameMat = new THREE.MeshStandardMaterial({ color: 0x0b1322, metalness: 0.8, roughness: 0.3 });
      const glassMat = new THREE.MeshPhysicalMaterial({
        color: 0x7dd3fc,
        transparent: true,
        opacity: 0.2,
        roughness: 0.1,
        transmission: 0.9,
        thickness: 0.2
      });

      // Glass Wall on East (X = CONFIG.floorWidth / 2)
      const eastX = CONFIG.floorWidth / 2;
      const glassPane = new THREE.Mesh(new THREE.BoxGeometry(0.1, CONFIG.wallHeight, CONFIG.floorDepth), glassMat);
      glassPane.position.set(eastX, CONFIG.wallHeight / 2, 0);
      parent.add(glassPane);

      // Vertical Window Mullions
      for (let z = -CONFIG.floorDepth / 2 + 3; z < CONFIG.floorDepth / 2; z += 4.5) {
        const post = new THREE.Mesh(new THREE.BoxGeometry(0.3, CONFIG.wallHeight, 0.3), frameMat);
        post.position.set(eastX - 0.1, CONFIG.wallHeight / 2, z);
        parent.add(post);
      }

      // Horizontal Window Transom
      const transom = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.25, CONFIG.floorDepth), frameMat);
      transom.position.set(eastX - 0.1, 4.2, 0);
      parent.add(transom);

      // Outside 3D City Skyline (Skyscrapers with glowing windows)
      const skylineGroup = new THREE.Group();
      skylineGroup.position.set(eastX + 16, 0, 0);

      const bldgColors = [0x09101f, 0x0c1529, 0x111c36];
      const winCanvas = document.createElement('canvas');
      winCanvas.width = 128;
      winCanvas.height = 256;
      const wCtx = winCanvas.getContext('2d');
      wCtx.fillStyle = '#080d1a';
      wCtx.fillRect(0, 0, 128, 256);
      wCtx.fillStyle = '#fef08a';
      for (let y = 10; y < 250; y += 12) {
        for (let x = 8; x < 120; x += 14) {
          if (Math.random() > 0.45) {
            wCtx.fillRect(x, y, 7, 7);
          }
        }
      }
      const winTex = new THREE.CanvasTexture(winCanvas);
      winTex.wrapS = THREE.RepeatWrapping;
      winTex.wrapT = THREE.RepeatWrapping;
      winTex.repeat.set(2, 6);

      const bldgMat = new THREE.MeshStandardMaterial({
        map: winTex,
        roughness: 0.6,
        metalness: 0.4,
        emissive: 0xfef08a,
        emissiveIntensity: 0.15
      });

      // Generate cluster of skyscrapers
      for (let i = 0; i < 28; i++) {
        const height = 12 + Math.random() * 24;
        const width = 3 + Math.random() * 3.5;
        const depth = 3 + Math.random() * 3.5;
        const bldg = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), bldgMat);
        const z = -CONFIG.floorDepth / 2 - 5 + Math.random() * (CONFIG.floorDepth + 10);
        const x = Math.random() * 20;
        bldg.position.set(x, height / 2 - 2, z);
        skylineGroup.add(bldg);
      }
      parent.add(skylineGroup);
    }

    // -----------------------------------------------------------------------
    // Glass Meeting Room
    // -----------------------------------------------------------------------
    createMeetingRoom(parent) {
      const roomGroup = new THREE.Group();
      roomGroup.position.set(-8.5, 0, -6.5);

      const glassMat = new THREE.MeshPhysicalMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.25,
        transmission: 0.85,
        roughness: 0.15
      });
      const frameMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.4 });

      // Glass partition walls
      const glassFront = new THREE.Mesh(new THREE.BoxGeometry(6.5, 3.8, 0.08), glassMat);
      glassFront.position.set(0, 1.9, 3.2);
      roomGroup.add(glassFront);

      const glassSide = new THREE.Mesh(new THREE.BoxGeometry(0.08, 3.8, 6.4), glassMat);
      glassSide.position.set(3.2, 1.9, 0);
      roomGroup.add(glassSide);

      // Conference Table
      const tableMat = new THREE.MeshStandardMaterial({ color: 0x1f2937, roughness: 0.3, metalness: 0.2 });
      const table = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.12, 1.8), tableMat);
      table.position.set(0, 1.1, 0);
      table.castShadow = true;
      roomGroup.add(table);

      // Table Legs
      [-1.8, 1.8].forEach(x => {
        const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.1, 16), frameMat);
        leg.position.set(x, 0.55, 0);
        leg.castShadow = true;
        roomGroup.add(leg);
      });

      // Meeting Room Presentation TV Screen
      const tvCanvas = document.createElement('canvas');
      tvCanvas.width = 512;
      tvCanvas.height = 288;
      const tvCtx = tvCanvas.getContext('2d');
      tvCtx.fillStyle = '#0f172a';
      tvCtx.fillRect(0, 0, 512, 288);
      tvCtx.fillStyle = '#38bdf8';
      tvCtx.font = 'bold 28px Cairo, sans-serif';
      tvCtx.fillText('PriceZ Autonomous Sprint #42', 30, 60);
      tvCtx.fillStyle = '#10b981';
      tvCtx.fillRect(30, 90, 320, 20);
      tvCtx.fillStyle = '#a855f7';
      tvCtx.fillRect(30, 125, 240, 20);
      tvCtx.fillStyle = '#38bdf8';
      tvCtx.fillRect(30, 160, 420, 20);

      const tvTex = new THREE.CanvasTexture(tvCanvas);
      const tvMat = new THREE.MeshStandardMaterial({
        map: tvTex,
        roughness: 0.2,
        emissive: 0x38bdf8,
        emissiveIntensity: 0.3
      });
      const tv = new THREE.Mesh(new THREE.BoxGeometry(3.2, 1.8, 0.1), tvMat);
      tv.position.set(0, 2.4, -3.1);
      roomGroup.add(tv);

      parent.add(roomGroup);
    }

    // -----------------------------------------------------------------------
    // Server Room with Glowing LED Indicators
    // -----------------------------------------------------------------------
    createServerRoom(parent) {
      const serverGroup = new THREE.Group();
      serverGroup.position.set(-1.5, 0, -8.5);

      const rackMat = new THREE.MeshStandardMaterial({ color: 0x090d16, metalness: 0.8, roughness: 0.4 });

      for (let i = 0; i < 3; i++) {
        const rack = new THREE.Mesh(new THREE.BoxGeometry(1.2, 3.2, 0.9), rackMat);
        rack.position.set(i * 1.5 - 1.5, 1.6, 0);
        rack.castShadow = true;
        serverGroup.add(rack);

        // Blinking LED panels
        const ledCanvas = document.createElement('canvas');
        ledCanvas.width = 128;
        ledCanvas.height = 256;
        const lCtx = ledCanvas.getContext('2d');
        lCtx.fillStyle = '#05080f';
        lCtx.fillRect(0, 0, 128, 256);

        for (let y = 10; y < 250; y += 14) {
          lCtx.fillStyle = Math.random() > 0.3 ? '#00f2fe' : '#10b981';
          lCtx.fillRect(15, y, 6, 6);
          lCtx.fillStyle = Math.random() > 0.5 ? '#8b5cf6' : '#38bdf8';
          lCtx.fillRect(35, y, 6, 6);
          lCtx.fillStyle = '#10b981';
          lCtx.fillRect(55, y, 6, 6);
        }

        const ledTex = new THREE.CanvasTexture(ledCanvas);
        const ledMat = new THREE.MeshStandardMaterial({
          map: ledTex,
          emissive: 0x00f2fe,
          emissiveIntensity: 0.5,
          roughness: 0.3
        });
        const ledPanel = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 2.8), ledMat);
        ledPanel.position.set(i * 1.5 - 1.5, 1.6, 0.46);
        serverGroup.add(ledPanel);
      }

      parent.add(serverGroup);
    }

    // -----------------------------------------------------------------------
    // Lounge Area (Modern Sofa, Coffee Table & Area Rug)
    // -----------------------------------------------------------------------
    createLoungeArea(parent) {
      const loungeGroup = new THREE.Group();
      loungeGroup.position.set(4.5, 0, -5.5);

      // Area Rug
      const rugMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.9 });
      const rug = new THREE.Mesh(new THREE.PlaneGeometry(5.5, 4.5), rugMat);
      rug.rotation.x = -Math.PI / 2;
      rug.position.set(0, 0.02, 0);
      rug.receiveShadow = true;
      loungeGroup.add(rug);

      // L-Shaped Leather Couch (Midnight Navy)
      const couchMat = new THREE.MeshStandardMaterial({ color: 0x111c33, roughness: 0.5, metalness: 0.1 });
      
      // Main Couch section
      const couchBase = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.5, 1.1), couchMat);
      couchBase.position.set(0, 0.35, 1.2);
      couchBase.castShadow = true;
      loungeGroup.add(couchBase);

      const couchBack = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.8, 0.3), couchMat);
      couchBack.position.set(0, 0.85, 1.65);
      couchBack.castShadow = true;
      loungeGroup.add(couchBack);

      // Chaise section
      const chaise = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.5, 2.2), couchMat);
      chaise.position.set(1.25, 0.35, 0.1);
      chaise.castShadow = true;
      loungeGroup.add(chaise);

      // Coffee Table (Oak & Glass)
      const tableMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.3 });
      const coffeeTable = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.4, 1.0), tableMat);
      coffeeTable.position.set(-0.2, 0.25, 0);
      coffeeTable.castShadow = true;
      loungeGroup.add(coffeeTable);

      parent.add(loungeGroup);
    }

    // -----------------------------------------------------------------------
    // Coffee & Refreshments Bar
    // -----------------------------------------------------------------------
    createCoffeeBar(parent) {
      const barGroup = new THREE.Group();
      barGroup.position.set(11.5, 0, -5.5);

      // Bar Counter
      const counterMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.3, metalness: 0.2 });
      const counter = new THREE.Mesh(new THREE.BoxGeometry(3.2, 1.1, 1.1), counterMat);
      counter.position.set(0, 0.55, 0);
      counter.castShadow = true;
      barGroup.add(counter);

      // Espresso Machine
      const machineMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8, roughness: 0.2 });
      const machine = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.6, 0.6), machineMat);
      machine.position.set(-0.6, 1.4, 0);
      machine.castShadow = true;
      barGroup.add(machine);

      // Water Dispenser Cooler
      const coolerBody = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 1.0, 16), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.5 }));
      coolerBody.position.set(1.0, 0.5, 0);
      barGroup.add(coolerBody);

      const waterBottle = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.6, 16), new THREE.MeshPhysicalMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.65, roughness: 0.1 }));
      waterBottle.position.set(1.0, 1.25, 0);
      barGroup.add(waterBottle);

      // Bar Stools
      [-1.0, 0, 1.0].forEach(x => {
        const stool = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.08, 16), new THREE.MeshStandardMaterial({ color: 0x0284c7 }));
        stool.position.set(x, 0.75, 1.1);
        stool.castShadow = true;
        barGroup.add(stool);

        const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.75, 12), new THREE.MeshStandardMaterial({ color: 0x0f172a }));
        leg.position.set(x, 0.375, 1.1);
        barGroup.add(leg);
      });

      parent.add(barGroup);
    }

    // -----------------------------------------------------------------------
    // Office Foliage & Potted Plants
    // -----------------------------------------------------------------------
    createOfficePlants(parent) {
      const plantLocations = [
        { x: -14, z: -8 },
        { x: -14, z: 8 },
        { x: 13, z: -8 },
        { x: 13, z: 8 },
        { x: -4, z: 7 },
        { x: 5, z: 7 },
        { x: 0, z: -2 }
      ];

      plantLocations.forEach(loc => {
        const plantGroup = new THREE.Group();
        plantGroup.position.set(loc.x, 0, loc.z);

        // Ceramic White Pot
        const pot = new THREE.Mesh(
          new THREE.CylinderGeometry(0.35, 0.25, 0.8, 16),
          new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.3 })
        );
        pot.position.set(0, 0.4, 0);
        pot.castShadow = true;
        plantGroup.add(pot);

        // Plant Foliage (Spherical Monstera / Bush layers)
        const leafMat = new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.7 });
        const bush1 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.55, 1), leafMat);
        bush1.position.set(0, 1.05, 0);
        bush1.castShadow = true;
        plantGroup.add(bush1);

        const bush2 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.4, 1), leafMat);
        bush2.position.set(0.2, 1.35, -0.1);
        plantGroup.add(bush2);

        parent.add(plantGroup);
      });
    }

    // -----------------------------------------------------------------------
    // Workstations (Desks, Chairs, Monitors, Keyboards & Hologram Rings)
    // -----------------------------------------------------------------------
    initWorkstations() {
      const stationSpecs = [
        { id: 'sales', name: 'Sales Station', x: -7, z: 2, rotY: 0, type: 'laptop' },
        { id: 'report', name: 'Report Station', x: -7, z: 6, rotY: 0, type: 'dual' },
        { id: 'support', name: 'Support Station', x: 1, z: 5, rotY: 0, type: 'desktop' },
        { id: 'content', name: 'Content Station', x: 8, z: 5, rotY: 0, type: 'desktop' },
        { id: 'research', name: 'Research Station', x: 8, z: 1, rotY: 0, type: 'ultrabook' },
        { id: 'architect', name: 'DevOps & Architect', x: -1, z: -6, rotY: Math.PI, type: 'triple' }
      ];

      stationSpecs.forEach(spec => {
        const wsGroup = new THREE.Group();
        wsGroup.position.set(spec.x, 0, spec.z);
        wsGroup.rotation.y = spec.rotY;

        // 1. Desk Top
        const deskTopMat = new THREE.MeshStandardMaterial({ color: CONFIG.colors.deskWood, roughness: 0.4 });
        const deskTop = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.1, 1.2), deskTopMat);
        deskTop.position.set(0, 1.05, 0);
        deskTop.castShadow = true;
        deskTop.receiveShadow = true;
        wsGroup.add(deskTop);

        // Desk Metal Legs
        const legMat = new THREE.MeshStandardMaterial({ color: 0x090d16, metalness: 0.8, roughness: 0.3 });
        [[-1.0, -0.45], [1.0, -0.45], [-1.0, 0.45], [1.0, 0.45]].forEach(pos => {
          const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 1.05, 12), legMat);
          leg.position.set(pos[0], 0.525, pos[1]);
          leg.castShadow = true;
          wsGroup.add(leg);
        });

        // 2. Ergonomic Office Mesh Chair
        const chair = this.createOfficeChair();
        chair.position.set(0, 0, 1.1);
        wsGroup.add(chair);

        // 3. Computer Display & Animated Screen
        const monitorData = this.createComputerSetup(spec.type);
        monitorData.group.position.set(0, 1.1, -0.2);
        wsGroup.add(monitorData.group);

        if (monitorData.screenMesh) {
          this.animatedMonitors.push({
            agentId: spec.id,
            mesh: monitorData.screenMesh,
            canvas: monitorData.canvas,
            ctx: monitorData.ctx,
            texture: monitorData.texture,
            type: spec.type
          });
        }

        // 4. Interactive Clickable Hitbox for Workstation
        const hitBox = new THREE.Mesh(
          new THREE.BoxGeometry(2.6, 2.0, 2.4),
          new THREE.MeshBasicMaterial({ transparent: true, opacity: 0 })
        );
        hitBox.position.set(0, 1.0, 0.4);
        hitBox.userData = { type: 'workstation', agentId: spec.id };
        wsGroup.add(hitBox);
        this.clickableObjects.push(hitBox);

        // 5. 3D Neon Floor Hologram Ring (Isometric Disc)
        const ringGeo = new THREE.RingGeometry(1.2, 1.35, 32);
        const ringMat = new THREE.MeshBasicMaterial({
          color: CONFIG.colors.cyanGlow,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.45
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = -Math.PI / 2;
        ring.position.set(0, 0.03, 0.5);
        wsGroup.add(ring);

        this.scene.add(wsGroup);
        this.workstations.set(spec.id, {
          group: wsGroup,
          ring: ring,
          chair: chair,
          chairPos: new THREE.Vector3(spec.x, 0, spec.z + 1.1)
        });
      });
    }

    createOfficeChair() {
      const chairGroup = new THREE.Group();
      const seatMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.7 });
      const chromeMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8, roughness: 0.2 });

      // Seat Cushion
      const seat = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.1, 0.65), seatMat);
      seat.position.set(0, 0.65, 0);
      seat.castShadow = true;
      chairGroup.add(seat);

      // Backrest
      const back = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.8, 0.1), seatMat);
      back.position.set(0, 1.1, 0.3);
      back.castShadow = true;
      chairGroup.add(back);

      // Piston & Star Base
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.6, 12), chromeMat);
      post.position.set(0, 0.32, 0);
      chairGroup.add(post);

      const base = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.05, 5), chromeMat);
      base.position.set(0, 0.05, 0);
      chairGroup.add(base);

      return chairGroup;
    }

    createComputerSetup(type) {
      const group = new THREE.Group();
      const pcMat = new THREE.MeshStandardMaterial({ color: 0x090d16, metalness: 0.7, roughness: 0.3 });

      // Canvas for dynamic monitor screen streaming
      const canvas = document.createElement('canvas');
      canvas.width = 512;
      canvas.height = 288;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#070c18';
      ctx.fillRect(0, 0, 512, 288);
      ctx.fillStyle = '#00f2fe';
      ctx.font = 'bold 24px monospace';
      ctx.fillText('> PriceZ Autonomous Agent', 25, 50);

      const texture = new THREE.CanvasTexture(canvas);
      const screenMat = new THREE.MeshBasicMaterial({ map: texture });
      let screenMesh = null;

      if (type === 'dual') {
        // Dual Curved Widescreen Monitors
        [-0.6, 0.6].forEach(xOff => {
          const monitor = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.55, 0.04), pcMat);
          monitor.position.set(xOff, 0.45, 0);
          monitor.rotation.y = xOff > 0 ? -0.2 : 0.2;
          group.add(monitor);

          const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 0.5), screenMat);
          scr.position.set(xOff, 0.45, 0.025);
          scr.rotation.y = xOff > 0 ? -0.2 : 0.2;
          group.add(scr);
          screenMesh = scr;
        });
      } else {
        // Single Desktop / Laptop Monitor
        const monitor = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.6, 0.04), pcMat);
        monitor.position.set(0, 0.45, 0);
        group.add(monitor);

        const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.95, 0.55), screenMat);
        scr.position.set(0, 0.45, 0.025);
        group.add(scr);
        screenMesh = scr;

        const stand = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.2, 0.2), pcMat);
        stand.position.set(0, 0.1, 0);
        group.add(stand);
      }

      // Keyboard & Mouse
      const keyboard = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.02, 0.2), pcMat);
      keyboard.position.set(0, 0.02, 0.3);
      group.add(keyboard);

      const mouse = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.03, 0.12), pcMat);
      mouse.position.set(0.45, 0.02, 0.3);
      group.add(mouse);

      return { group, screenMesh, canvas, ctx, texture };
    }

    // -----------------------------------------------------------------------
    // 3D AI Employee Characters (Articulated Hierarchical Models)
    // -----------------------------------------------------------------------
    initCharacters() {
      const charSpecs = [
        {
          id: 'sales',
          name: 'Sales Agent',
          role: 'وكيل المبيعات والتسويق',
          avatar: '💼',
          color: CONFIG.colors.cyanGlow,
          outfitColor: 0x1e293b,
          hairColor: 0x1e1b4b,
          headset: false,
          glasses: true,
          deskWaypoint: 'chair_sales',
          deskCoord: { x: -7, y: 0, z: 2 }
        },
        {
          id: 'report',
          name: 'Report Agent',
          role: 'وكيل التقارير والإحصائيات',
          avatar: '📊',
          color: CONFIG.colors.purpleGlow,
          outfitColor: 0x312e81,
          hairColor: 0x3b0764,
          headset: false,
          glasses: false,
          deskWaypoint: 'chair_report',
          deskCoord: { x: -7, y: 0, z: 6 }
        },
        {
          id: 'support',
          name: 'Support Agent',
          role: 'وكيل الدعم الفني والخدمة',
          avatar: '🎧',
          color: CONFIG.colors.blueGlow,
          outfitColor: 0x0369a1,
          hairColor: 0x0284c7, // Hijab
          headset: true,
          glasses: false,
          deskWaypoint: 'chair_support',
          deskCoord: { x: 1, y: 0, z: 5 }
        },
        {
          id: 'content',
          name: 'Content Agent',
          role: 'وكيل صناعة المحتوى',
          avatar: '✍️',
          color: CONFIG.colors.purpleGlow,
          outfitColor: 0x4c1d95,
          hairColor: 0x701a75,
          headset: true,
          glasses: false,
          deskWaypoint: 'chair_content',
          deskCoord: { x: 8, y: 0, z: 5 }
        },
        {
          id: 'research',
          name: 'Research Agent',
          role: 'وكيل البحث والتحليل',
          avatar: '🔍',
          color: CONFIG.colors.emeraldGlow,
          outfitColor: 0x064e3b,
          hairColor: 0x1c1917,
          headset: false,
          glasses: true,
          deskWaypoint: 'chair_research',
          deskCoord: { x: 8, y: 0, z: 1 }
        },
        {
          id: 'architect',
          name: 'Architect & DevOps',
          role: 'المخطط والمعمار البرمجي',
          avatar: '🏛️',
          color: CONFIG.colors.cyanGlow,
          outfitColor: 0x0f172a,
          hairColor: 0x334155,
          headset: false,
          glasses: false,
          deskWaypoint: 'chair_architect',
          deskCoord: { x: -1, y: 0, z: -6 }
        }
      ];

      charSpecs.forEach(spec => {
        const char = new AgentCharacter3D(spec, this);
        this.agents.set(spec.id, char);
        this.scene.add(char.group);
        this.clickableObjects.push(char.hitBox);
      });
    }

    // -----------------------------------------------------------------------
    // Interactive Raycasting & Selection
    // -----------------------------------------------------------------------
    initInteraction() {
      const dom = this.renderer.domElement;

      dom.addEventListener('mousemove', (e) => {
        const rect = dom.getBoundingClientRect();
        this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.clickableObjects, true);

        if (intersects.length > 0) {
          dom.style.cursor = 'pointer';
          const target = intersects[0].object.userData;
          if (target && target.agentId && this.hoveredObject !== target.agentId) {
            this.hoveredObject = target.agentId;
            this.setWorkstationGlow(target.agentId, true);
          }
        } else {
          dom.style.cursor = 'default';
          if (this.hoveredObject) {
            this.setWorkstationGlow(this.hoveredObject, false);
            this.hoveredObject = null;
          }
        }
      });

      dom.addEventListener('click', () => {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.clickableObjects, true);

        if (intersects.length > 0) {
          const target = intersects[0].object.userData;
          if (target && target.agentId) {
            this.selectAgent(target.agentId);
          }
        }
      });
    }

    setWorkstationGlow(agentId, isGlow) {
      const ws = this.workstations.get(agentId);
      if (ws && ws.ring) {
        ws.ring.material.opacity = isGlow ? 0.9 : 0.45;
        ws.ring.scale.set(isGlow ? 1.15 : 1.0, isGlow ? 1.15 : 1.0, 1.0);
      }
    }

    selectAgent(agentId) {
      this.selectedAgentId = agentId;
      console.log('[Office3D] Selected agent:', agentId);

      // Smooth camera transition to focus on agent
      this.focusCameraOnAgent(agentId);

      // Open UI Slide-Over Detail Drawer
      if (typeof window.openAgentDrawer === 'function') {
        window.openAgentDrawer(agentId);
      }
    }

    focusCameraOnAgent(agentId) {
      const char = this.agents.get(agentId);
      if (!char) return;

      const pos = char.group.position;
      const targetPos = new THREE.Vector3(pos.x, 1.4, pos.z);
      const cameraTargetPos = new THREE.Vector3(pos.x + 3.5, 4.2, pos.z + 4.5);

      this.tweenCamera(cameraTargetPos, targetPos, 1200);
    }

    setCameraPreset(presetName) {
      const p = CONFIG.cameraPresets[presetName];
      if (!p) return;
      this.tweenCamera(new THREE.Vector3(p.pos.x, p.pos.y, p.pos.z), new THREE.Vector3(p.target.x, p.target.y, p.target.z), 1500);
    }

    tweenCamera(targetCamPos, targetControlsTarget, duration = 1200) {
      if (typeof TWEEN !== 'undefined') {
        new TWEEN.Tween(this.camera.position)
          .to(targetCamPos, duration)
          .easing(TWEEN.Easing.Cubic.Out)
          .start();

        new TWEEN.Tween(this.controls.target)
          .to(targetControlsTarget, duration)
          .easing(TWEEN.Easing.Cubic.Out)
          .start();
      } else {
        this.camera.position.copy(targetCamPos);
        this.controls.target.copy(targetControlsTarget);
      }
    }

    // -----------------------------------------------------------------------
    // Backend Real-Time State Integration
    // -----------------------------------------------------------------------
    syncAgentState(agentId, data) {
      const char = this.agents.get(agentId);
      if (!char) return;

      char.updateState(data);

      // Update monitor screen
      const mon = this.animatedMonitors.find(m => m.agentId === agentId);
      if (mon && data.status === 'working') {
        this.updateMonitorScreen(mon, data);
      }
    }

    renameAgent(agentId, newName, newRole) {
      const char = this.agents.get(agentId);
      if (!char) return;
      if (newName) char.spec.name = newName;
      if (newRole) char.spec.role = newRole;
      char.redrawHUD();
    }

    updateMonitorScreen(mon, data) {
      const ctx = mon.ctx;
      ctx.fillStyle = '#070c18';
      ctx.fillRect(0, 0, 512, 288);

      ctx.fillStyle = '#00f2fe';
      ctx.font = 'bold 20px monospace';
      ctx.fillText(`> Agent: ${data.agent_id || mon.agentId}`, 20, 40);

      ctx.fillStyle = '#38bdf8';
      ctx.font = '16px monospace';
      ctx.fillText(`Task: ${(data.active_task || data.step_details || 'Running...').slice(0, 35)}`, 20, 80);

      // Mini Progress bar
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(20, 110, 470, 20);
      ctx.fillStyle = '#10b981';
      ctx.fillRect(20, 110, (data.progress || 30) * 4.7, 20);

      // Code matrix lines
      ctx.fillStyle = '#64748b';
      ctx.font = '13px monospace';
      ctx.fillText('import asyncio, json, pricez_core', 20, 170);
      ctx.fillText('await agent_loop.execute_pipeline()', 20, 200);
      ctx.fillText('✓ verified OWASP security boundaries', 20, 230);

      mon.texture.needsUpdate = true;
    }

    // -----------------------------------------------------------------------
    // Main Render Loop (60 FPS)
    // -----------------------------------------------------------------------
    animate() {
      requestAnimationFrame(() => this.animate());

      const delta = this.clock.getDelta();
      const time = this.clock.getElapsedTime();

      if (typeof TWEEN !== 'undefined') {
        TWEEN.update();
      }

      this.controls.update();

      // Update Characters (Rig animations & waypoint navigation)
      this.agents.forEach(agent => {
        agent.update(delta, time, this.camera);
      });

      this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
      if (!this.container || !this.renderer || !this.camera) return;
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    }
  }

  // =========================================================================
  // 3. 3D AGENT CHARACTER (Articulated Hierarchical Model & Rig Animation)
  // =========================================================================
  class AgentCharacter3D {
    constructor(spec, engine) {
      this.spec = spec;
      this.engine = engine;
      this.id = spec.id;

      this.state = 'idle'; // 'idle', 'working', 'thinking', 'done', 'error'
      this.subState = 'SITTING'; // 'SITTING', 'WALKING', 'STANDING'
      this.progress = 0;
      this.activeTask = '';

      this.group = new THREE.Group();
      this.group.position.set(spec.deskCoord.x, 0, spec.deskCoord.z + 1.1);

      // Navigation & Pathfinding State
      this.currentWaypoint = spec.deskWaypoint;
      this.targetWaypoint = null;
      this.pathQueue = [];
      this.moveSpeed = 2.2;
      this.idleTimer = Math.random() * 8 + 6;

      this.buildSkeletonMesh();
      this.buildOverheadHUD();
    }

    buildSkeletonMesh() {
      const outfitMat = new THREE.MeshStandardMaterial({ color: this.spec.outfitColor, roughness: 0.6 });
      const skinMat = new THREE.MeshStandardMaterial({ color: 0xffdbac, roughness: 0.5 });
      const darkMat = new THREE.MeshStandardMaterial({ color: 0x090d16, roughness: 0.8 });
      const hairMat = new THREE.MeshStandardMaterial({ color: this.spec.hairColor, roughness: 0.7 });

      // Root Pelvis
      this.pelvis = new THREE.Group();
      this.pelvis.position.y = 0.65; // Sitting height default
      this.group.add(this.pelvis);

      // Torso / Jacket
      this.torso = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.65, 0.35), outfitMat);
      this.torso.position.y = 0.35;
      this.torso.castShadow = true;
      this.pelvis.add(this.torso);

      // Neck & Head
      this.neck = new THREE.Group();
      this.neck.position.y = 0.38;
      this.torso.add(this.neck);

      this.head = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.42, 0.36), skinMat);
      this.head.position.y = 0.24;
      this.head.castShadow = true;
      this.neck.add(this.head);

      // Hair or Hijab
      const hair = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.25, 0.4), hairMat);
      hair.position.y = 0.14;
      this.head.add(hair);

      // Accessories: Glasses / Headset
      if (this.spec.glasses) {
        const glasses = new THREE.Mesh(
          new THREE.BoxGeometry(0.34, 0.08, 0.05),
          new THREE.MeshBasicMaterial({ color: 0x00f2fe })
        );
        glasses.position.set(0, 0.02, 0.19);
        this.head.add(glasses);
      }

      if (this.spec.headset) {
        const headset = new THREE.Mesh(
          new THREE.TorusGeometry(0.24, 0.03, 8, 24),
          new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.8 })
        );
        headset.rotation.z = Math.PI / 2;
        headset.position.y = 0.05;
        this.head.add(headset);
      }

      // Arms: Left Shoulder & Arm
      this.leftShoulder = new THREE.Group();
      this.leftShoulder.position.set(-0.35, 0.28, 0);
      this.torso.add(this.leftShoulder);

      this.leftUpperArm = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.32, 0.14), outfitMat);
      this.leftUpperArm.position.y = -0.16;
      this.leftShoulder.add(this.leftUpperArm);

      this.leftForearm = new THREE.Group();
      this.leftForearm.position.y = -0.16;
      this.leftUpperArm.add(this.leftForearm);

      const lHand = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.28, 0.12), skinMat);
      lHand.position.y = -0.14;
      this.leftForearm.add(lHand);

      // Arms: Right Shoulder & Arm
      this.rightShoulder = new THREE.Group();
      this.rightShoulder.position.set(0.35, 0.28, 0);
      this.torso.add(this.rightShoulder);

      this.rightUpperArm = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.32, 0.14), outfitMat);
      this.rightUpperArm.position.y = -0.16;
      this.rightShoulder.add(this.rightUpperArm);

      this.rightForearm = new THREE.Group();
      this.rightForearm.position.y = -0.16;
      this.rightUpperArm.add(this.rightForearm);

      const rHand = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.28, 0.12), skinMat);
      rHand.position.y = -0.14;
      this.rightForearm.add(rHand);

      // Legs: Left Thigh & Shin
      this.leftHip = new THREE.Group();
      this.leftHip.position.set(-0.16, -0.05, 0);
      this.pelvis.add(this.leftHip);

      this.leftThigh = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.38, 0.16), darkMat);
      this.leftThigh.position.y = -0.19;
      this.leftHip.add(this.leftThigh);

      this.leftKnee = new THREE.Group();
      this.leftKnee.position.y = -0.19;
      this.leftThigh.add(this.leftKnee);

      const lShin = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.36, 0.14), darkMat);
      lShin.position.y = -0.18;
      this.leftKnee.add(lShin);

      // Legs: Right Thigh & Shin
      this.rightHip = new THREE.Group();
      this.rightHip.position.set(0.16, -0.05, 0);
      this.pelvis.add(this.rightHip);

      this.rightThigh = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.38, 0.16), darkMat);
      this.rightThigh.position.y = -0.19;
      this.rightHip.add(this.rightThigh);

      this.rightKnee = new THREE.Group();
      this.rightKnee.position.y = -0.19;
      this.rightThigh.add(this.rightKnee);

      const rShin = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.36, 0.14), darkMat);
      rShin.position.y = -0.18;
      this.rightKnee.add(rShin);

      // Invisible Raycast Hitbox
      this.hitBox = new THREE.Mesh(
        new THREE.CylinderGeometry(0.45, 0.45, 1.8, 12),
        new THREE.MeshBasicMaterial({ transparent: true, opacity: 0 })
      );
      this.hitBox.position.y = 0.9;
      this.hitBox.userData = { type: 'character', agentId: this.id };
      this.group.add(this.hitBox);
    }

    buildOverheadHUD() {
      // 3D Billboard Canvas Texture for Agent HUD
      this.hudCanvas = document.createElement('canvas');
      this.hudCanvas.width = 384;
      this.hudCanvas.height = 128;
      this.hudCtx = this.hudCanvas.getContext('2d');

      this.hudTexture = new THREE.CanvasTexture(this.hudCanvas);
      const hudMat = new THREE.MeshBasicMaterial({
        map: this.hudTexture,
        transparent: true,
        depthWrite: false
      });

      this.hudMesh = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.55), hudMat);
      this.hudMesh.position.y = 2.15;
      this.group.add(this.hudMesh);

      this.redrawHUD();
    }

    redrawHUD() {
      const ctx = this.hudCtx;
      ctx.clearRect(0, 0, 384, 128);

      // Pill Background with Frosted Glass Look
      ctx.fillStyle = 'rgba(7, 11, 20, 0.88)';
      ctx.beginPath();
      ctx.roundRect(10, 10, 364, 108, 24);
      ctx.fill();

      // Border with Accent Color
      ctx.strokeStyle = this.state === 'working' ? '#00f2fe' : (this.state === 'done' ? '#10b981' : '#38bdf8');
      ctx.lineWidth = 4;
      ctx.stroke();

      // Status Dot
      ctx.fillStyle = this.state === 'working' ? '#00f2fe' : (this.state === 'done' ? '#10b981' : '#34d399');
      ctx.beginPath();
      ctx.arc(42, 60, 10, 0, Math.PI * 2);
      ctx.fill();

      // Agent Name
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 28px Cairo, sans-serif';
      ctx.fillText(this.spec.name, 64, 52);

      // Status Pill / Task Progress
      ctx.font = 'bold 20px monospace';
      if (this.state === 'working') {
        ctx.fillStyle = '#00f2fe';
        ctx.fillText(`[Working ${this.progress}%]`, 64, 85);
      } else if (this.state === 'done') {
        ctx.fillStyle = '#10b981';
        ctx.fillText('[✓ Completed]', 64, 85);
      } else {
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('[Idle / Ready]', 64, 85);
      }

      this.hudTexture.needsUpdate = true;
    }

    updateState(data) {
      if (data.name) {
        this.spec.name = data.name;
      }
      if (data.role) {
        this.spec.role = data.role;
      }
      this.state = data.status || 'idle';
      this.progress = data.progress || 0;
      this.activeTask = data.active_task || data.step_details || '';

      if (this.state === 'working') {
        // Must return to workstation chair immediately
        this.navigateTo(this.spec.deskWaypoint);
      }

      this.redrawHUD();
    }

    navigateTo(destWaypointKey) {
      if (this.currentWaypoint === destWaypointKey) return;
      this.targetWaypoint = destWaypointKey;

      // Simple routing: if not adjacent, route via corridor
      const dest = WAYPOINTS[destWaypointKey];
      if (dest) {
        this.targetPos = new THREE.Vector3(dest.x, 0, dest.z);
        this.subState = 'WALKING';
      }
    }

    update(delta, time, camera) {
      // 1. Face HUD towards Camera
      if (this.hudMesh) {
        this.hudMesh.quaternion.copy(camera.quaternion);
      }

      // 2. State Machine: Working vs Idle vs Walking
      if (this.state === 'working') {
        if (this.subState !== 'WALKING') {
          this.subState = 'SITTING';
          this.animateTyping(time);
        } else {
          this.animateWalking(time, delta);
        }
      } else if (this.state === 'done') {
        this.animateCelebrating(time);
      } else {
        // IDLE STATE
        if (this.subState === 'WALKING') {
          this.animateWalking(time, delta);
        } else if (this.subState === 'SITTING') {
          this.animateSittingIdle(time);
          this.idleTimer -= delta;
          if (this.idleTimer <= 0) {
            this.idleTimer = Math.random() * 15 + 12;
            this.decideIdleAction();
          }
        } else {
          this.animateStandingIdle(time);
          this.idleTimer -= delta;
          if (this.idleTimer <= 0) {
            this.idleTimer = Math.random() * 15 + 12;
            this.decideIdleAction();
          }
        }
      }
    }

    decideIdleAction() {
      // Pick random social destination: coffee bar, window, lounge, or return to desk
      const destinations = ['coffee_bar', 'lounge_sofa', 'panoramic_window', this.spec.deskWaypoint];
      const nextDest = destinations[Math.floor(Math.random() * destinations.length)];
      this.navigateTo(nextDest);
    }

    // -----------------------------------------------------------------------
    // Skeletal Rig Animations
    // -----------------------------------------------------------------------
    animateTyping(time) {
      this.pelvis.position.y = 0.62;
      this.leftHip.rotation.x = -Math.PI / 2;
      this.rightHip.rotation.x = -Math.PI / 2;
      this.leftKnee.rotation.x = Math.PI / 2;
      this.rightKnee.rotation.x = Math.PI / 2;

      this.torso.rotation.x = 0.08;
      this.leftShoulder.rotation.x = -0.7;
      this.rightShoulder.rotation.x = -0.7;

      // Fast typing motion with alternate wrist tapping
      this.leftForearm.rotation.x = -0.6 + Math.sin(time * 22) * 0.12;
      this.rightForearm.rotation.x = -0.6 + Math.cos(time * 22) * 0.12;

      this.head.rotation.x = 0.25 + Math.sin(time * 3) * 0.03;
      this.head.rotation.y = 0;
    }

    animateSittingIdle(time) {
      this.pelvis.position.y = 0.62;
      this.leftHip.rotation.x = -Math.PI / 2;
      this.rightHip.rotation.x = -Math.PI / 2;
      this.leftKnee.rotation.x = Math.PI / 2;
      this.rightKnee.rotation.x = Math.PI / 2;

      this.torso.rotation.x = -0.04;
      this.leftShoulder.rotation.x = -0.2;
      this.rightShoulder.rotation.x = -0.2;
      this.leftForearm.rotation.x = -0.4;
      this.rightForearm.rotation.x = -0.4;

      // Gentle breathing & looking around
      this.head.rotation.x = 0.05;
      this.head.rotation.y = Math.sin(time * 0.8) * 0.2;
    }

    animateStandingIdle(time) {
      this.pelvis.position.y = 1.05;
      this.leftHip.rotation.x = 0;
      this.rightHip.rotation.x = 0;
      this.leftKnee.rotation.x = 0;
      this.rightKnee.rotation.x = 0;

      this.torso.rotation.x = 0;
      this.leftShoulder.rotation.x = 0;
      this.rightShoulder.rotation.x = 0;
      this.leftForearm.rotation.x = 0;
      this.rightForearm.rotation.x = 0;

      this.head.rotation.y = Math.sin(time * 0.6) * 0.25;
    }

    animateWalking(time, delta) {
      this.pelvis.position.y = 1.05 + Math.abs(Math.sin(time * 8)) * 0.06;

      // Legs pendulum swing
      const stride = Math.sin(time * 9);
      this.leftHip.rotation.x = stride * 0.65;
      this.rightHip.rotation.x = -stride * 0.65;

      this.leftKnee.rotation.x = Math.max(0, -stride * 0.75);
      this.rightKnee.rotation.x = Math.max(0, stride * 0.75);

      // Arm counter swing
      this.leftShoulder.rotation.x = -stride * 0.55;
      this.rightShoulder.rotation.x = stride * 0.55;
      this.leftForearm.rotation.x = -0.2;
      this.rightForearm.rotation.x = -0.2;

      // Move towards target position
      if (this.targetPos) {
        const dir = new THREE.Vector3().subVectors(this.targetPos, this.group.position);
        dir.y = 0;
        const dist = dir.length();

        if (dist > 0.25) {
          dir.normalize();
          this.group.position.addScaledVector(dir, this.moveSpeed * delta);

          // Smooth rotation towards travel heading
          const targetAngle = Math.atan2(dir.x, dir.z);
          this.group.rotation.y = THREE.MathUtils.lerp(this.group.rotation.y, targetAngle, 0.15);
        } else {
          // Arrived at destination
          this.currentWaypoint = this.targetWaypoint;
          this.targetWaypoint = null;
          this.targetPos = null;

          if (this.currentWaypoint.startsWith('chair_')) {
            this.subState = 'SITTING';
            this.group.rotation.y = 0; // Face computer desk
          } else {
            this.subState = 'STANDING';
          }
        }
      }
    }

    animateCelebrating(time) {
      this.pelvis.position.y = 1.05 + Math.abs(Math.sin(time * 10)) * 0.1;
      this.leftHip.rotation.x = 0;
      this.rightHip.rotation.x = 0;

      // Both arms raised high in victory
      this.leftShoulder.rotation.x = -2.6;
      this.rightShoulder.rotation.x = -2.6;
      this.leftShoulder.rotation.z = 0.5;
      this.rightShoulder.rotation.z = -0.5;

      this.head.rotation.x = -0.2;
    }
  }

  // Expose to window
  window.Office3DEngine = Office3DEngine;

})(window);
