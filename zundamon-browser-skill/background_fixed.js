/**
 * Zundamon Voice for Claude - Background Service Worker (CORS修正版)
 * VOICEVOX APIを直接呼び出してCORS問題を回避
 */

chrome.runtime.onInstalled.addListener(() => {
  console.log('🔊 Zundamon Voice for Claude: インストール完了');
  
  chrome.storage.sync.set({
    enabled: true,
    voicevoxAPI: 'http://localhost:50021',
    speakerID: 3
  });
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSettings') {
    chrome.storage.sync.get(['enabled', 'voicevoxAPI', 'speakerID'], (settings) => {
      sendResponse(settings);
    });
    return true;
  }
  
  // 音声合成リクエスト
  if (request.action === 'synthesize') {
    synthesizeAudio(request.text, request.speakerID)
      .then(audioData => {
        sendResponse({ success: true, audioData: audioData });
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
    return true; // 非同期レスポンス
  }
});

async function synthesizeAudio(text, speakerID) {
  const voicevoxAPI = 'http://localhost:50021';
  
  try {
    // 1. 音声クエリ生成
    const queryUrl = `${voicevoxAPI}/audio_query?text=${encodeURIComponent(text)}&speaker=${speakerID}`;
    const queryResponse = await fetch(queryUrl, { method: 'POST' });
    
    if (!queryResponse.ok) {
      throw new Error(`音声クエリ失敗: ${queryResponse.status}`);
    }
    
    const audioQuery = await queryResponse.json();
    
    // 2. 音声合成
    const synthesisUrl = `${voicevoxAPI}/synthesis?speaker=${speakerID}`;
    const synthesisResponse = await fetch(synthesisUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(audioQuery)
    });
    
    if (!synthesisResponse.ok) {
      throw new Error(`音声合成失敗: ${synthesisResponse.status}`);
    }
    
    const audioBuffer = await synthesisResponse.arrayBuffer();
    
    // ArrayBufferをArrayに変換（メッセージング用）
    return Array.from(new Uint8Array(audioBuffer));
    
  } catch (error) {
    console.error('Background音声合成エラー:', error);
    throw error;
  }
}
