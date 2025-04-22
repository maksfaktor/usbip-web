/**
 * OrangeUSB - Основной JavaScript файл
 */

// Проверка готовности DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('OrangeUSB Web Interface - Готов к работе');
    
    // Инициализация Bootstrap тултипов
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Автоматическое скрытие сообщений через 5 секунд
    const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Обработчик поиска информации об устройстве
    const deviceSearchForm = document.getElementById('device-search-form');
    if (deviceSearchForm) {
        deviceSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const deviceId = document.getElementById('device_id').value.trim();
            
            if (!deviceId) {
                showNotification('Введите идентификатор устройства', 'warning');
                return;
            }
            
            // Показываем индикатор загрузки
            const resultContainer = document.getElementById('device-info-result');
            resultContainer.innerHTML = '<div class="text-center p-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Загрузка...</span></div><p class="mt-2">Поиск информации...</p></div>';
            
            // Отправляем запрос на сервер
            fetch('/search_device_info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'device_id': deviceId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultContainer.innerHTML = `
                        <div class="alert alert-success mb-3" role="alert">
                            <h5 class="alert-heading">Информация найдена</h5>
                            <hr>
                            <div class="device-info-text">
                                ${data.data.replace(/\n/g, '<br>')}
                            </div>
                            <hr>
                            <button class="btn btn-sm btn-outline-success copy-device-info">
                                <i class="fas fa-copy me-1"></i>Копировать
                            </button>
                            <button class="btn btn-sm btn-outline-primary save-device-info" data-device-id="${deviceId}">
                                <i class="fas fa-save me-1"></i>Сохранить
                            </button>
                        </div>
                    `;
                    
                    // Добавляем обработчик копирования
                    document.querySelector('.copy-device-info').addEventListener('click', function() {
                        const textToCopy = data.data;
                        navigator.clipboard.writeText(textToCopy).then(() => {
                            showNotification('Информация скопирована в буфер обмена', 'success');
                        }).catch(err => {
                            showNotification('Не удалось скопировать текст: ' + err, 'danger');
                        });
                    });
                    
                    // Добавляем обработчик сохранения
                    document.querySelector('.save-device-info').addEventListener('click', function() {
                        const busid = this.getAttribute('data-device-id');
                        const modal = new bootstrap.Modal(document.getElementById('saveDeviceInfoModal'));
                        document.getElementById('save_busid').value = busid;
                        document.getElementById('save_device_info').value = data.data;
                        modal.show();
                    });
                } else {
                    resultContainer.innerHTML = `
                        <div class="alert alert-warning" role="alert">
                            <h5 class="alert-heading">Информация не найдена</h5>
                            <p>${data.message}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                resultContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <h5 class="alert-heading">Ошибка</h5>
                        <p>Произошла ошибка при выполнении запроса: ${error}</p>
                    </div>
                `;
            });
        });
    }
});

/**
 * Вспомогательная функция для отображения уведомлений
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип уведомления (success, danger, warning, info)
 */
function showNotification(message, type = 'info') {
    // Проверяем, есть ли контейнер для уведомлений
    let container = document.getElementById('notification-container');
    
    // Если контейнера нет, создаем его
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '5000';
        document.body.appendChild(container);
    }
    
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `toast align-items-center text-white bg-${type} border-0`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    notification.setAttribute('aria-atomic', 'true');
    
    // Формируем содержимое уведомления
    notification.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Добавляем уведомление в контейнер
    container.appendChild(notification);
    
    // Инициализируем и показываем уведомление
    const toast = new bootstrap.Toast(notification, {
        autohide: true,
        delay: 5000
    });
    toast.show();
    
    // Удаляем уведомление после скрытия
    notification.addEventListener('hidden.bs.toast', function() {
        notification.remove();
    });
}
