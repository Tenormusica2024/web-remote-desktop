/**
 * Zundamon Voice for Claude - Background Service Worker
 * CORS回避のためのプロキシ機能を提供
 */

chrome.runtime.onInstalled.addListener(() => {
  console.log('🔊 Zundamon Voice for Claude: インストール完了');
  
  // デフォルト設定
  chrome.storage.sync.set({
    enabled: true,
    voicevoxAPI: 'http://localhost:50021',
    speakerID: 3
  });
});

// コンテンツスクリプトからのメッセージ処理
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSettings') {
    chrome.storage.sync.get(['enabled', 'voicevoxAPI', 'speakerID'], (settings) => {
      sendResponse(settings);
    });
    return true;
  }
  
  // VOICEVOX APIプロキシ
  if (request.action === 'voicevox_proxy') {
    const { url, method, body, headers } = request;
    
    fetch(url, {
      method: method || 'POST',
      headers: headers || {},
      body: body
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.arrayBuffer();
    })
    .then(data => {
      sendResponse({ success: true, data: Array.from(new Uint8Array(data)) });
    })
    .catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    
    return true; // 非同期レスポンス
  }
});
