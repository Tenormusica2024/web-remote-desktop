/**
 * Zundamon Voice for Claude - Content Script
 * Claude AIの応答を監視して音声読み上げを実行
 */

class ZundamonVoiceController {
  constructor() {
    this.voicevoxAPI = 'http://localhost:50021';
    this.speakerID = 3; // ずんだもん ノーマル
    this.isEnabled = true;
    this.lastProcessedText = '';
    this.audioContext = null;
    this.observer = null;
    
    this.init();
  }
  
  async init() {
    // 設定読み込み
    const settings = await chrome.storage.sync.get(['enabled']);
    this.isEnabled = settings.enabled !== false;
    
    // Audio Context初期化
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // Claude応答監視開始
    this.startObserving();
    
    console.log('🔊 Zundamon Voice for Claude: 起動完了');
  }
  
  startObserving() {
    // Claudeの応答メッセージを監視
    this.observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            this.checkForClaudeResponse(node);
          }
        });
      });
    });
    
    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
  
  checkForClaudeResponse(element) {
    if (!this.isEnabled) return;
    
    // Claudeの応答メッセージを検出
    // claude.aiのDOM構造に応じて調整が必要な場合あり
    const messageSelectors = [
      '[data-test-render-count]', // Claude応答の典型的なセレクタ
      '.font-claude-message',
      '[class*="Message"]',
      '[class*="message"]'
    ];
    
    for (const selector of messageSelectors) {
      if (element.matches && element.matches(selector)) {
        this.processClaudeMessage(element);
        return;
      }
      
      const messages = element.querySelectorAll(selector);
      messages.forEach(msg => this.processClaudeMessage(msg));
    }
  }
  
  processClaudeMessage(element) {
    // テキスト抽出
    const text = this.extractText(element);
    
    if (!text || text === this.lastProcessedText) {
      return; // 既に処理済み
    }
    
    // 長すぎるテキストは要約
    const textToSpeak = this.summarizeIfNeeded(text);
    
    if (textToSpeak.length > 0) {
      this.lastProcessedText = text;
      this.speakText(textToSpeak);
    }
  }
  
  extractText(element) {
    // コードブロックやツール実行結果を除外
    const clone = element.cloneNode(true);
    
    // 不要な要素を削除
    const excludeSelectors = ['pre', 'code', '[class*="tool"]', '[class*="thinking"]'];
    excludeSelectors.forEach(selector => {
      clone.querySelectorAll(selector).forEach(el => el.remove());
    });
    
    return clone.textContent.trim();
  }
  
  summarizeIfNeeded(text) {
    // 100文字以内に要約
    if (text.length <= 100) {
      return text;
    }
    
    // 最初の文を取得
    const firstSentence = text.split(/[。．\n]/)[0];
    if (firstSentence.length <= 100) {
      return firstSentence;
    }
    
    return text.substring(0, 97) + '...';
  }
  
  async speakText(text) {
    try {
      console.log(`🔊 音声合成開始: ${text}`);
      
      // 1. 音声クエリ生成（Background経由でCORS回避）
      const queryUrl = `${this.voicevoxAPI}/audio_query?text=${encodeURIComponent(text)}&speaker=${this.speakerID}`;
      const queryResult = await this.proxyFetch(queryUrl, 'POST');
      
      if (!queryResult.success) {
        throw new Error(`音声クエリ失敗: ${queryResult.error}`);
      }
      
      const audioQuery = new TextDecoder().decode(new Uint8Array(queryResult.data));
      
      // 2. 音声合成（Background経由でCORS回避）
      const synthesisUrl = `${this.voicevoxAPI}/synthesis?speaker=${this.speakerID}`;
      const synthesisResult = await this.proxyFetch(
        synthesisUrl,
        'POST',
        audioQuery,
        { 'Content-Type': 'application/json' }
      );
      
      if (!synthesisResult.success) {
        throw new Error(`音声合成失敗: ${synthesisResult.error}`);
      }
      
      const audioData = new Uint8Array(synthesisResult.data).buffer;
      
      // 3. Web Audio APIで再生
      await this.playAudio(audioData);
      
      console.log('✅ 音声再生完了');
      
    } catch (error) {
      console.error('❌ 音声合成エラー:', error);
      // VOICEVOX未起動時のエラーは静かに無視
      if (!error.message.includes('Failed to fetch')) {
        this.showNotification('音声再生失敗', error.message);
      }
    }
  }
  
  async proxyFetch(url, method, body, headers) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({
        action: 'voicevox_proxy',
        url: url,
        method: method,
        body: body,
        headers: headers || {}
      }, (response) => {
        resolve(response);
      });
    });
  }
  
  async playAudio(arrayBuffer) {
    const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);
    
    return new Promise((resolve) => {
      source.onended = resolve;
      source.start(0);
    });
  }
  
  showNotification(title, message) {
    // 簡易通知（開発用）
    console.warn(`[${title}] ${message}`);
  }
  
  async setEnabled(enabled) {
    this.isEnabled = enabled;
    await chrome.storage.sync.set({ enabled });
    console.log(`🔊 音声通知: ${enabled ? '有効' : '無効'}`);
  }
}

// 拡張機能起動
const zundamon = new ZundamonVoiceController();

// メッセージリスナー（popup.htmlからの制御用）
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'toggle') {
    zundamon.setEnabled(request.enabled);
    sendResponse({ success: true });
  } else if (request.action === 'speak') {
    zundamon.speakText(request.text);
    sendResponse({ success: true });
  }
  return true;
});
