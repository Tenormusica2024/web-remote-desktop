/**
 * Zundamon Voice for Claude - Content Script (CORS修正版)
 * Background Service Worker経由でVOICEVOX APIを呼び出し
 */

class ZundamonVoiceController {
  constructor() {
    this.voicevoxAPI = 'http://localhost:50021';
    this.speakerID = 3;
    this.isEnabled = true;
    this.lastProcessedText = '';
    this.audioContext = null;
    this.observer = null;
    
    this.init();
  }
  
  async init() {
    const settings = await chrome.storage.sync.get(['enabled']);
    this.isEnabled = settings.enabled !== false;
    
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    this.startObserving();
    
    console.log('🔊 Zundamon Voice for Claude: 起動完了');
  }
  
  startObserving() {
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
    
    const messageSelectors = [
      '[data-test-render-count]',
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
    const text = this.extractText(element);
    
    if (!text || text === this.lastProcessedText) {
      return;
    }
    
    const textToSpeak = this.summarizeIfNeeded(text);
    
    if (textToSpeak.length > 0) {
      this.lastProcessedText = text;
      this.speakText(textToSpeak);
    }
  }
  
  extractText(element) {
    const clone = element.cloneNode(true);
    
    const excludeSelectors = ['pre', 'code', '[class*="tool"]', '[class*="thinking"]'];
    excludeSelectors.forEach(selector => {
      clone.querySelectorAll(selector).forEach(el => el.remove());
    });
    
    return clone.textContent.trim();
  }
  
  summarizeIfNeeded(text) {
    if (text.length <= 100) {
      return text;
    }
    
    const firstSentence = text.split(/[。．\n]/)[0];
    if (firstSentence.length <= 100) {
      return firstSentence;
    }
    
    return text.substring(0, 97) + '...';
  }
  
  async speakText(text) {
    try {
      console.log(`🔊 音声合成開始: ${text}`);
      
      // Background Service Worker経由でAPI呼び出し
      const result = await this.synthesizeViaBackground(text);
      
      if (!result.success) {
        throw new Error(result.error);
      }
      
      // ArrayBufferに変換
      const audioData = new Uint8Array(result.audioData).buffer;
      
      // 再生
      await this.playAudio(audioData);
      
      console.log('✅ 音声再生完了');
      
    } catch (error) {
      console.error('❌ 音声合成エラー:', error);
    }
  }
  
  async synthesizeViaBackground(text) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({
        action: 'synthesize',
        text: text,
        speakerID: this.speakerID
      }, (response) => {
        resolve(response || { success: false, error: 'No response' });
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
    console.warn(`[${title}] ${message}`);
  }
  
  async setEnabled(enabled) {
    this.isEnabled = enabled;
    await chrome.storage.sync.set({ enabled });
    console.log(`🔊 音声通知: ${enabled ? '有効' : '無効'}`);
  }
}

const zundamon = new ZundamonVoiceController();

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'toggle') {
    zundamon.setEnabled(request.enabled);
    sendResponse({ success: true });
  }
  return true;
});
