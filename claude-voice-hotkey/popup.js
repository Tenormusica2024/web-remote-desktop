/**
 * Claude Voice Hotkey - Popup Script
 * 設定画面の制御
 */

const enabledToggle = document.getElementById('enabled');
const mouseButtonSelect = document.getElementById('mouseButton');
const autoSendToggle = document.getElementById('autoSend');
const statusDiv = document.getElementById('status');

// 設定読み込み
chrome.storage.sync.get(['enabled', 'mouseButton', 'autoSend'], (result) => {
  enabledToggle.checked = result.enabled !== undefined ? result.enabled : true;
  mouseButtonSelect.value = result.mouseButton || 'side1';
  autoSendToggle.checked = result.autoSend !== undefined ? result.autoSend : true;
  
  statusDiv.textContent = '✅ 設定読み込み完了';
  statusDiv.className = 'status success';
});

// 設定変更イベント
enabledToggle.addEventListener('change', saveSettings);
mouseButtonSelect.addEventListener('change', saveSettings);
autoSendToggle.addEventListener('change', saveSettings);

function saveSettings() {
  const settings = {
    enabled: enabledToggle.checked,
    mouseButton: mouseButtonSelect.value,
    autoSend: autoSendToggle.checked
  };
  
  chrome.storage.sync.set(settings, () => {
    statusDiv.textContent = '✅ 設定保存完了';
    statusDiv.className = 'status success';
    
    console.log('⚙️ 設定保存:', settings);
    
    // 3秒後にステータスをリセット
    setTimeout(() => {
      statusDiv.textContent = 'マウスサイドボタンで音声入力を制御できます';
      statusDiv.className = 'status';
    }, 3000);
  });
}
