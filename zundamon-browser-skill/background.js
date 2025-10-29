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
  console.log('🔧 [Background] メッセージ受信:', request.action, sender.tab?.id);
  
  if (request.action === 'getSettings') {
    chrome.storage.sync.get(['enabled', 'voicevoxAPI', 'speakerID'], (settings) => {
      console.log('🔧 [Background] 設定返却:', settings);
      sendResponse(settings);
    });
    return true;
  }
  
  // 音声合成リクエスト
  if (request.action === 'synthesize') {
    console.log('🔧 [Background] 音声合成リクエスト受信:', { text: request.text, speakerID: request.speakerID });
    
    synthesizeAudio(request.text, request.speakerID)
      .then(audioData => {
        console.log('✅ [Background] 音声合成成功、レスポンス送信:', audioData.length, 'bytes');
        sendResponse({ success: true, audioData: audioData });
      })
      .catch(error => {
        console.error('❌ [Background] 音声合成失敗、エラーレスポンス送信:', error.message);
        sendResponse({ success: false, error: error.message });
      });
    return true; // 非同期レスポンス
  }
  
  console.warn('⚠️ [Background] 未知のアクション:', request.action);
});

async function synthesizeAudio(text, speakerID) {
  const voicevoxAPI = 'http://localhost:50021';
  
  console.log('🔧 [Background] synthesizeAudio開始:', { text, speakerID });
  
  try {
    // 1. 音声クエリ生成
    const queryUrl = `${voicevoxAPI}/audio_query?text=${encodeURIComponent(text)}&speaker=${speakerID}`;
    console.log('🔧 [Background] audio_query開始:', queryUrl);
    
    const queryResponse = await fetch(queryUrl, { method: 'POST' });
    console.log('🔧 [Background] audio_query完了:', queryResponse.status, queryResponse.ok);
    
    if (!queryResponse.ok) {
      throw new Error(`音声クエリ失敗: ${queryResponse.status}`);
    }
    
    const audioQuery = await queryResponse.json();
    console.log('🔧 [Background] audioQuery取得完了:', Object.keys(audioQuery));
    
    // 2. 音声合成
    const synthesisUrl = `${voicevoxAPI}/synthesis?speaker=${speakerID}`;
    console.log('🔧 [Background] synthesis開始:', synthesisUrl);
    
    const synthesisResponse = await fetch(synthesisUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(audioQuery)
    });
    console.log('🔧 [Background] synthesis完了:', synthesisResponse.status, synthesisResponse.ok);
    
    if (!synthesisResponse.ok) {
      throw new Error(`音声合成失敗: ${synthesisResponse.status}`);
    }
    
    const audioBuffer = await synthesisResponse.arrayBuffer();
    console.log('🔧 [Background] audioBuffer取得完了:', audioBuffer.byteLength, 'bytes');
    
    // ArrayBufferをArrayに変換（メッセージング用）
    const result = Array.from(new Uint8Array(audioBuffer));
    console.log('✅ [Background] synthesizeAudio成功:', result.length, 'bytes');
    return result;
    
  } catch (error) {
    console.error('❌ [Background] 音声合成エラー:', error);
    console.error('❌ [Background] エラー詳細:', error.message, error.stack);
    throw error;
  }
}
