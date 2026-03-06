/**
 * Configuración page — Aesthetic settings + floor plan colors + status colors
 * All stored in localStorage
 */

document.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('hk-theme') || 'dark';
    const fontSize = localStorage.getItem('hk-font-size') || 'medium';
    const accent = localStorage.getItem('hk-accent') || '#63b3ed';

    setActiveOption('themeOptions', theme);
    setActiveOption('fontSizeOptions', fontSize);
    setActiveColor(accent);

    // Glow toggle
    const glow = localStorage.getItem('hk-glow') || 'on';
    setActiveOption('glowOptions', glow);

    loadFloorPlanColors();
    loadStatusColors();
});


function setTheme(value) {
    document.documentElement.setAttribute('data-theme', value);
    localStorage.setItem('hk-theme', value);
    setActiveOption('themeOptions', value);
    showToast(`Tema cambiado a ${value === 'dark' ? 'oscuro' : 'claro'}`, 'success');
}


function setFontSize(value) {
    document.documentElement.setAttribute('data-font-size', value);
    localStorage.setItem('hk-font-size', value);
    setActiveOption('fontSizeOptions', value);
    showToast('Tamaño de fuente actualizado', 'success');
}


function setGlow(value) {
    if (value === 'off') {
        document.body.setAttribute('data-glow', 'off');
    } else {
        document.body.removeAttribute('data-glow');
    }
    localStorage.setItem('hk-glow', value);
    setActiveOption('glowOptions', value);
    showToast(value === 'on' ? 'Degradado activado' : 'Degradado desactivado', 'success');
}


function setAccent(color) {
    document.documentElement.style.setProperty('--accent', color);
    document.documentElement.style.setProperty('--accent-hover', darken(color, 15));
    localStorage.setItem('hk-accent', color);
    setActiveColor(color);
    showToast('Color de acento actualizado', 'success');
}


// ── Floor Plan Colors ───────────────────────────────────────

function loadFloorPlanColors() {
    const roomColor = localStorage.getItem('hk-fp-room') || '#F2D06B';
    const corridorColor = localStorage.getItem('hk-fp-corridor') || '#9E9E9E';
    const frameColor = localStorage.getItem('hk-fp-frame') || '#FFFFFF';

    updatePicker('fpRoomColor', 'fpRoomHex', roomColor);
    updatePicker('fpCorridorColor', 'fpCorridorHex', corridorColor);
    updatePicker('fpFrameColor', 'fpFrameHex', frameColor);
}


function setFloorPlanColor(type, color) {
    color = color.toUpperCase();
    const root = document.documentElement;

    if (type === 'room') {
        root.style.setProperty('--fp-room', color);
        root.style.setProperty('--fp-room-occupied', darken(color, 12));
        localStorage.setItem('hk-fp-room', color);
        updatePicker('fpRoomColor', 'fpRoomHex', color);
    } else if (type === 'corridor') {
        root.style.setProperty('--fp-corridor', color);
        localStorage.setItem('hk-fp-corridor', color);
        updatePicker('fpCorridorColor', 'fpCorridorHex', color);
    } else if (type === 'frame') {
        root.style.setProperty('--fp-frame', color);
        localStorage.setItem('hk-fp-frame', color);
        updatePicker('fpFrameColor', 'fpFrameHex', color);
    }

    showToast('Color del plano actualizado', 'success');
}


// ── Status Colors ───────────────────────────────────────────

function loadStatusColors() {
    const available = localStorage.getItem('hk-status-available') || '#48BB78';
    const occupied = localStorage.getItem('hk-status-occupied') || '#ED8936';
    const maintenance = localStorage.getItem('hk-status-maintenance') || '#3D1C1C';

    updatePicker('fpStatusAvailable', 'fpStatusAvailableHex', available);
    updatePicker('fpStatusOccupied', 'fpStatusOccupiedHex', occupied);
    updatePicker('fpStatusMaintenance', 'fpStatusMaintenanceHex', maintenance);
}


function setStatusColor(status, color) {
    color = color.toUpperCase();
    const root = document.documentElement;

    if (status === 'available') {
        root.style.setProperty('--status-available', color);
        localStorage.setItem('hk-status-available', color);
        updatePicker('fpStatusAvailable', 'fpStatusAvailableHex', color);
    } else if (status === 'occupied') {
        root.style.setProperty('--status-occupied', color);
        localStorage.setItem('hk-status-occupied', color);
        updatePicker('fpStatusOccupied', 'fpStatusOccupiedHex', color);
    } else if (status === 'maintenance') {
        root.style.setProperty('--fp-maintenance', color);
        root.style.setProperty('--status-maintenance', color);
        localStorage.setItem('hk-status-maintenance', color);
        updatePicker('fpStatusMaintenance', 'fpStatusMaintenanceHex', color);
    }

    showToast('Color de estado actualizado', 'success');
}


// ── Reset ───────────────────────────────────────────────────

function resetSettings() {
    // Theme + font + accent
    const keys = [
        'hk-theme', 'hk-font-size', 'hk-accent', 'hk-glow',
        'hk-fp-room', 'hk-fp-corridor', 'hk-fp-frame',
        'hk-status-available', 'hk-status-occupied', 'hk-status-maintenance'
    ];
    keys.forEach(k => localStorage.removeItem(k));

    document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.setAttribute('data-font-size', 'medium');

    const props = [
        '--accent', '--accent-hover',
        '--fp-room', '--fp-room-occupied', '--fp-corridor', '--fp-frame',
        '--status-available', '--status-occupied', '--fp-maintenance', '--status-maintenance'
    ];
    props.forEach(p => document.documentElement.style.removeProperty(p));

    setActiveOption('themeOptions', 'dark');
    setActiveOption('fontSizeOptions', 'medium');
    setActiveColor('#63b3ed');
    setActiveOption('glowOptions', 'on');
    document.body.removeAttribute('data-glow');
    loadFloorPlanColors();
    loadStatusColors();

    showToast('Configuración restablecida', 'info');
}


// ── Helpers ─────────────────────────────────────────────────

function updatePicker(pickerId, hexId, color) {
    const picker = document.getElementById(pickerId);
    const hex = document.getElementById(hexId);
    if (picker) picker.value = color;
    if (hex) hex.textContent = color.toUpperCase();
}

function setActiveOption(containerId, value) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.querySelectorAll('.setting-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.value === value);
    });
}

function setActiveColor(color) {
    document.querySelectorAll('#accentOptions .color-swatch').forEach(sw => {
        sw.classList.toggle('active', sw.dataset.value === color);
    });
}

function darken(hex, percent) {
    const num = parseInt(hex.replace('#', ''), 16);
    const r = Math.max(0, (num >> 16) - Math.round(2.55 * percent));
    const g = Math.max(0, ((num >> 8) & 0x00FF) - Math.round(2.55 * percent));
    const b = Math.max(0, (num & 0x0000FF) - Math.round(2.55 * percent));
    return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1).toUpperCase()}`;
}
