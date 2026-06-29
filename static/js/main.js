/**
 * Упрощенная версия для локального мониторинга поступающих
 * С ограничением частоты обновлений
 */

let currentGraph = null;
let isUpdating = false;
let config = {};
let lastForceRefresh = 0;

// ============================================
// ЗАГРУЗКА КОНФИГУРАЦИИ
// ============================================

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        config = await response.json();
        console.log('✅ Конфигурация загружена');
        
        if (config.auto_refresh_interval) {
            setInterval(() => {
                console.log('🔄 Автообновление...');
                loadData(false);
            }, config.auto_refresh_interval);
        }
        
        if (config.max_force_refresh_per_hour) {
            console.log(`🛡️ Максимум принудительных обновлений: ${config.max_force_refresh_per_hour} в час`);
        }
    } catch (error) {
        console.warn('⚠️ Не удалось загрузить конфигурацию');
        setInterval(() => loadData(false), 600000);
    }
}

// ============================================
// ЗАГРУЗКА ДАННЫХ
// ============================================

async function loadData(force = false) {
    if (isUpdating) {
        console.log('⏳ Обновление уже выполняется...');
        return;
    }
    
    if (force) {
        const now = Date.now();
        if (now - lastForceRefresh < 5000) {
            alert('⏳ Пожалуйста, подождите 5 секунд между обновлениями');
            return;
        }
        lastForceRefresh = now;
    }
    
    isUpdating = true;
    const btn = document.getElementById('refresh-btn');
    btn.textContent = '⏳ Загрузка...';
    btn.disabled = true;
    
    try {
        const url = `/api/data${force ? '?force=true' : ''}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.status === 429) {
            alert('⚠️ ' + data.error);
            return;
        }
        
        if (data.error) {
            alert('❌ Ошибка: ' + data.error);
            return;
        }
        
        updateCards(data.cards, data.dynamics);
        updateGraph(data.graph);
        updateLastUpdate(data.last_update, data.cached, data.cache_ttl_minutes);
        
        console.log('✅ Данные обновлены:', new Date().toLocaleString());
        
    } catch (error) {
        console.error('❌ Ошибка:', error);
        alert('Не удалось загрузить данные. Проверьте соединение.');
    } finally {
        isUpdating = false;
        btn.textContent = '🔄 Обновить';
        btn.disabled = false;
    }
}

// ============================================
// ОБНОВЛЕНИЕ ИНТЕРФЕЙСА
// ============================================

function updateCards(cards, dynamics) {
    // Обновляем основные карточки
    document.getElementById('total').textContent = cards.total;
    document.getElementById('priority-1').textContent = cards.priority_1;
    document.getElementById('docs-submitted').textContent = cards.docs_submitted;
    document.getElementById('without-priority').textContent = cards.without_priority;
    
    // Обновляем карточку "Изменение с прошлого обновления"
    const changeDisplay = document.getElementById('change-display');
    const changeDetails = document.getElementById('change-details');
    
    if (dynamics && dynamics.has_history) {
        const totalChange = dynamics.total_change;
        const p1Change = dynamics.priority_1_change;
        
        // Показываем изменение общего числа
        const changeText = `${totalChange > 0 ? '+' : ''}${totalChange}`;
        changeDisplay.textContent = changeText;
        changeDisplay.className = `number ${totalChange >= 0 ? 'positive' : 'negative'}`;
        
        // Детали изменения
        let details = `Всего: ${totalChange > 0 ? '+' : ''}${totalChange}`;
        if (p1Change !== 0) {
            details += `, приоритет 1: ${p1Change > 0 ? '+' : ''}${p1Change}`;
        }
        changeDetails.textContent = details;
        changeDetails.className = `change ${totalChange >= 0 ? 'positive' : 'negative'}`;
    } else {
        changeDisplay.textContent = '—';
        changeDisplay.className = 'number';
        changeDetails.textContent = 'Нет истории (первый запуск)';
        changeDetails.className = 'change';
    }
    
    // Обновляем изменение в карточке "Всего подавших"
    const totalChange = document.getElementById('total-change');
    if (dynamics && dynamics.has_history) {
        const change = dynamics.total_change;
        const text = `${change > 0 ? '+' : ''}${change} с прошлого раза`;
        totalChange.textContent = text;
        totalChange.className = `change ${change >= 0 ? 'positive' : 'negative'}`;
    } else {
        totalChange.textContent = 'Нет истории (первый запуск)';
        totalChange.className = 'change';
    }
}

function updateGraph(graphJson) {
    const graphData = JSON.parse(graphJson);
    const chartDiv = document.getElementById('chart');
    
    if (currentGraph) {
        Plotly.react(chartDiv, graphData.data, graphData.layout);
    } else {
        Plotly.newPlot(chartDiv, graphData.data, graphData.layout);
        currentGraph = true;
    }
}

function updateLastUpdate(timestamp, cached, ttlMinutes) {
    const date = new Date(timestamp);
    const timeStr = date.toLocaleString('ru-RU');
    const status = cached ? '📂 Из кэша' : '🔄 Свежие данные';
    
    document.getElementById('last-update').textContent = 
        `Обновление: ${timeStr} (${status})`;
    
    document.getElementById('data-status').textContent = 
        `⏰ Кэш обновляется каждые ${ttlMinutes} минут`;
}

// ============================================
// ОБРАБОТЧИКИ
// ============================================

async function refreshData() {
    await loadData(true);
}

// ============================================
// ЗАПУСК
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Запуск мониторинга поступающих');
    await loadConfig();
    await loadData(false);
});

window.refreshData = refreshData;
window.loadData = loadData;