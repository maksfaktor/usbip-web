/**
 * Вспомогательная функция для отображения уведомлений
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип уведомления (success, danger, warning, info)
 */
function showNotification(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const newContainer = document.createElement('div');
        newContainer.id = 'toast-container';
        newContainer.className = 'toast-container';
        document.body.appendChild(newContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">${type === 'success' ? 'Успех' : type === 'danger' ? 'Ошибка' : type === 'warning' ? 'Предупреждение' : 'Информация'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Закрыть"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    document.getElementById('toast-container').innerHTML += toastHTML;
    
    const toastElement = document.getElementById(toastId);
    toastElement.classList.add(`text-bg-${type}`);
    
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Автоматическое удаление элемента после скрытия
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Инициализация всплывающих подсказок
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Обработчик для формы публикации USB устройства
 */
function bindDevice(busid) {
    // Используем URL из констант, переданных через шаблон
    fetch(URLS.bind_device, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ busid: busid })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Устройство успешно опубликовано', 'success');
            // Перезагрузка страницы для обновления списка устройств
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка публикации устройства: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

/**
 * Обработчик для формы подключения к удаленному серверу
 */
function getRemoteDevices() {
    const ipAddress = document.getElementById('remote_ip').value;
    
    if (!ipAddress) {
        showNotification('Пожалуйста, введите IP-адрес', 'warning');
        return;
    }
    
    // Показываем индикатор загрузки
    document.getElementById('remote-devices-spinner').classList.remove('d-none');
    document.getElementById('remote-devices-list').innerHTML = '';
    
    fetch(URLS.get_remote_devices, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ip: ipAddress })
    })
    .then(response => response.json())
    .then(data => {
        // Скрываем индикатор загрузки
        document.getElementById('remote-devices-spinner').classList.add('d-none');
        
        if (data.success) {
            if (data.devices && data.devices.length > 0) {
                let devicesList = '';
                
                data.devices.forEach(device => {
                    devicesList += `
                        <div class="card mb-3 device-card">
                            <div class="card-body">
                                <h5 class="card-title">${device.usbip_id}</h5>
                                <p class="card-text device-info">${device.description}</p>
                                <button onclick="attachDevice('${ipAddress}', '${device.busid}')" class="btn btn-success btn-sm">
                                    <i class="bi bi-usb-symbol"></i> Подключить
                                </button>
                            </div>
                        </div>
                    `;
                });
                
                document.getElementById('remote-devices-list').innerHTML = devicesList;
            } else {
                document.getElementById('remote-devices-list').innerHTML = '<div class="alert alert-info">Устройства не найдены</div>';
            }
        } else {
            document.getElementById('remote-devices-list').innerHTML = `<div class="alert alert-danger">Ошибка: ${data.message}</div>`;
        }
    })
    .catch(error => {
        document.getElementById('remote-devices-spinner').classList.add('d-none');
        document.getElementById('remote-devices-list').innerHTML = `<div class="alert alert-danger">Ошибка: ${error}</div>`;
    });
}

/**
 * Обработчик для формы подключения удаленного устройства
 */
function attachDevice(ip, busid) {
    fetch(URLS.attach_device, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ip: ip, busid: busid })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Устройство успешно подключено', 'success');
            // Перезагрузка страницы для обновления списка устройств
            setTimeout(() => window.location.href = '/', 1000);
        } else {
            showNotification('Ошибка подключения устройства: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

/**
 * Обработчик для отключения устройства
 */
function detachDevice(port) {
    fetch(URLS.detach_device, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ port: port })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Устройство успешно отключено', 'success');
            // Перезагрузка страницы для обновления списка устройств
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка отключения устройства: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}



/**
 * Обработчик для установки алиаса устройства
 */
function setDeviceAlias(busid) {
    const alias = prompt('Введите алиас для устройства:');
    
    if (alias === null) return; // Пользователь отменил
    
    if (!alias.trim()) {
        showNotification('Алиас не может быть пустым', 'warning');
        return;
    }
    
    fetch('/device-alias', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            busid: busid,
            alias: alias
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Алиас устройства установлен', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка установки алиаса: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

/**
 * Обработчик для установки имени порта
 */
function setPortName(portNumber) {
    const customName = prompt('Введите название для порта:');
    
    if (customName === null) return; // Пользователь отменил
    
    fetch('/port-name', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            port_number: portNumber,
            custom_name: customName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Название порта установлено', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка установки названия: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

/**
 * Обработчики для виртуальных устройств
 */
function createVirtualDevice() {
    const form = document.getElementById('virtual-device-form');
    const formData = new FormData(form);
    
    fetch('/virtual/create-device', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Виртуальное устройство успешно создано', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка создания устройства: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
    
    return false; // Предотвращаем стандартную отправку формы
}

function createVirtualPort(deviceId) {
    const portName = prompt('Введите название для порта:');
    
    if (portName === null) return; // Пользователь отменил
    
    if (!portName.trim()) {
        showNotification('Название порта не может быть пустым', 'warning');
        return;
    }
    
    fetch('/virtual/create-port', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            device_id: deviceId,
            name: portName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Виртуальный порт успешно создан', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка создания порта: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

function connectVirtualDevice(deviceId) {
    fetch('/virtual/connect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device_id: deviceId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Виртуальное устройство успешно подключено', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка подключения устройства: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

function disconnectVirtualDevice(deviceId) {
    fetch('/virtual/disconnect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device_id: deviceId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Виртуальное устройство успешно отключено', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка отключения устройства: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

function connectVirtualPort(portId) {
    fetch('/virtual/connect-port', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ port_id: portId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Виртуальный порт успешно подключен', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка подключения порта: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

function disconnectVirtualPort(portId) {
    fetch('/virtual/disconnect-port', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ port_id: portId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Виртуальный порт успешно отключен', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка отключения порта: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

function deleteVirtualDevice(deviceId) {
    if (!confirm('Вы уверены, что хотите удалить это виртуальное устройство?')) {
        return;
    }
    
    fetch('/virtual/delete-device', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device_id: deviceId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Виртуальное устройство успешно удалено', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка удаления устройства: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

function deleteVirtualPort(portId) {
    if (!confirm('Вы уверены, что хотите удалить этот виртуальный порт?')) {
        return;
    }
    
    fetch('/virtual/delete-port', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ port_id: portId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Виртуальный порт успешно удален', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Ошибка удаления порта: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showNotification('Произошла ошибка: ' + error, 'danger');
    });
}

/**
 * Обработчики для страницы логов
 */
function filterLogs() {
    const level = document.getElementById('log-level-filter').value;
    const source = document.getElementById('log-source-filter').value;
    const dateFrom = document.getElementById('log-date-from').value;
    const dateTo = document.getElementById('log-date-to').value;
    
    // Показываем все строки логов
    const logRows = document.querySelectorAll('#logs-table tbody tr');
    logRows.forEach(row => {
        row.style.display = 'table-row';
    });
    
    // Фильтрация по уровню
    if (level !== 'all') {
        logRows.forEach(row => {
            if (row.getAttribute('data-level') !== level) {
                row.style.display = 'none';
            }
        });
    }
    
    // Фильтрация по источнику
    if (source !== 'all') {
        logRows.forEach(row => {
            if (row.getAttribute('data-source') !== source && row.style.display !== 'none') {
                row.style.display = 'none';
            }
        });
    }
    
    // Фильтрация по дате (от)
    if (dateFrom) {
        const fromDate = new Date(dateFrom);
        logRows.forEach(row => {
            if (row.style.display !== 'none') {
                const rowDate = new Date(row.getAttribute('data-timestamp'));
                if (rowDate < fromDate) {
                    row.style.display = 'none';
                }
            }
        });
    }
    
    // Фильтрация по дате (до)
    if (dateTo) {
        const toDate = new Date(dateTo);
        toDate.setHours(23, 59, 59); // До конца дня
        logRows.forEach(row => {
            if (row.style.display !== 'none') {
                const rowDate = new Date(row.getAttribute('data-timestamp'));
                if (rowDate > toDate) {
                    row.style.display = 'none';
                }
            }
        });
    }
    
    // Подсчет видимых записей
    const visibleRows = document.querySelectorAll('#logs-table tbody tr[style="display: table-row"]').length;
    document.getElementById('logs-count').textContent = visibleRows;
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация подсказок
    initializeTooltips();
    
    // Инициализация фильтров логов если они есть на странице
    const logFilterForm = document.getElementById('log-filter-form');
    if (logFilterForm) {
        logFilterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            filterLogs();
        });
        
        // Сразу применяем фильтр при загрузке
        filterLogs();
    }
    
    // Инициализация формы виртуального устройства
    const virtualDeviceForm = document.getElementById('virtual-device-form');
    if (virtualDeviceForm) {
        virtualDeviceForm.addEventListener('submit', function(e) {
            e.preventDefault();
            createVirtualDevice();
        });
    }
    
    console.log("OrangeUSB Web Interface - Готов к работе");
});