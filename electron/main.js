/**
 * Hotel Karim — Electron Main Process
 * Starts the Flask backend server and opens the app in a desktop window.
 */
const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const net = require('net');

let mainWindow = null;
let flaskProcess = null;
const PORT = 5000;

// Determine Flask server path
function getFlaskPath() {
    if (app.isPackaged) {
        // In packaged app, the exe is in resources/flask-server/
        return path.join(process.resourcesPath, 'flask-server', 'hotel-karim', 'hotel-karim.exe');
    } else {
        // In development, use Python directly
        return null;
    }
}

// Start the Flask backend
function startFlask() {
    const flaskExe = getFlaskPath();

    if (flaskExe) {
        // Production: run bundled exe
        console.log('Starting Flask from:', flaskExe);
        flaskProcess = spawn(flaskExe, [], {
            cwd: path.dirname(flaskExe),
            stdio: 'pipe',
            windowsHide: true,
            env: { ...process.env, FLASK_PORT: String(PORT) }
        });
    } else {
        // Development: run with python
        const projectDir = path.join(__dirname, '..');
        flaskProcess = spawn('python', ['app.py'], {
            cwd: projectDir,
            stdio: 'pipe',
            windowsHide: true,
            env: { ...process.env, FLASK_PORT: String(PORT) }
        });
    }

    flaskProcess.stdout.on('data', (data) => {
        console.log(`Flask: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
        console.log(`Flask: ${data}`);
    });

    flaskProcess.on('error', (err) => {
        console.error('Failed to start Flask:', err);
        dialog.showErrorBox('Error', 'No se pudo iniciar el servidor del hotel.');
    });

    flaskProcess.on('exit', (code) => {
        console.log(`Flask process exited with code ${code}`);
        flaskProcess = null;
    });
}

// Wait for Flask to be ready
function waitForFlask(retries = 30) {
    return new Promise((resolve, reject) => {
        const check = (attempt) => {
            const socket = new net.Socket();
            socket.setTimeout(500);

            socket.on('connect', () => {
                socket.destroy();
                resolve();
            });

            socket.on('timeout', () => {
                socket.destroy();
                if (attempt < retries) {
                    setTimeout(() => check(attempt + 1), 500);
                } else {
                    reject(new Error('Flask server did not start in time'));
                }
            });

            socket.on('error', () => {
                socket.destroy();
                if (attempt < retries) {
                    setTimeout(() => check(attempt + 1), 500);
                } else {
                    reject(new Error('Flask server did not start'));
                }
            });

            socket.connect(PORT, '127.0.0.1');
        };
        check(0);
    });
}

// Create the main window
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 900,
        minHeight: 600,
        title: 'Hotel Karim',
        icon: path.join(__dirname, 'build', 'icon.ico'),
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
        show: false,
    });

    mainWindow.loadURL(`http://127.0.0.1:${PORT}`);

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// App lifecycle
app.on('ready', async () => {
    startFlask();

    try {
        await waitForFlask();
        createWindow();
    } catch (err) {
        dialog.showErrorBox('Error', 'El servidor no respondió a tiempo.\n' + err.message);
        app.quit();
    }
});

app.on('window-all-closed', () => {
    // Kill Flask when all windows are closed
    if (flaskProcess) {
        flaskProcess.kill();
        flaskProcess = null;
    }
    app.quit();
});

app.on('before-quit', () => {
    if (flaskProcess) {
        flaskProcess.kill();
        flaskProcess = null;
    }
});
