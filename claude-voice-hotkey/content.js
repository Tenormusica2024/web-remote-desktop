/**
 * Claude Voice Hotkey - Content Script
 * マウスサイドボタンでClaude.aiの音声入力を制御
 */

class ClaudeVoiceHotkey {
  constructor() {
    this.isRecording = false;
    this.voiceButton = null;
    this.settings = {
      enabled: true,
      mouseButton: 'side1', // 'side1' (Button 3) or 'side2' (Button 4) or 'both'
      autoSend: true
    };
    
    this.init();
  }
  
  async init() {
    console.log('🎤 Claude Voice Hotkey: 初期化開始');
    
    // 設定読み込み
    await this.loadSettings();
    
    // 5秒待機（ページ完全ロード待ち）
    await this.sleep(5000);
    
    // マウスイベント監視開始
    this.startMouseListener();
    
    console.log('✅ Claude Voice Hotkey: 初期化完了');
  }
  
  async loadSettings() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['enabled', 'mouseButton', 'autoSend'], (result) => {
        if (result.enabled !== undefined) this.settings.enabled = result.enabled;
        if (result.mouseButton) this.settings.mouseButton = result.mouseButton;
        if (result.autoSend !== undefined) this.settings.autoSend = result.autoSend;
        
        console.log('⚙️ 設定読み込み完了:', this.settings);
        resolve();
      });
    });
  }
  
  startMouseListener() {
    console.log('🖱️ マウスリスナー開始');
    
    // マウスボタン押下
    document.addEventListener('mousedown', (e) => {
      if (!this.settings.enabled) return;
      
      // サイドボタン判定
      const isTargetButton = this.isTargetMouseButton(e.button);
      
      if (isTargetButton && !this.isRecording) {
        console.log('🎤 音声入力開始（マウスボタン押下）');
        e.preventDefault();
        e.stopPropagation();
        this.startVoiceInput();
      }
    }, true);
    
    // マウスボタン離す
    document.addEventListener('mouseup', (e) => {
      if (!this.settings.enabled) return;
      
      const isTargetButton = this.isTargetMouseButton(e.button);
      
      if (isTargetButton && this.isRecording) {
        console.log('🎤 音声入力停止（マウスボタン離す）');
        e.preventDefault();
        e.stopPropagation();
        this.stopVoiceInput();
      }
    }, true);
  }
  
  isTargetMouseButton(button) {
    // button 3 = サイドボタン1（戻る）
    // button 4 = サイドボタン2（進む）
    
    if (this.settings.mouseButton === 'side1') {
      return button === 3;
    } else if (this.settings.mouseButton === 'side2') {
      return button === 4;
    } else if (this.settings.mouseButton === 'both') {
      return button === 3 || button === 4;
    }
    
    return false;
  }
  
  startVoiceInput() {
    // Claude.aiの音声入力ボタンを探す
    this.voiceButton = this.findVoiceButton();
    
    if (!this.voiceButton) {
      console.error('❌ 音声入力ボタンが見つかりません');
      return;
    }
    
    console.log('🔍 音声入力ボタン検出:', this.voiceButton);
    
    // 音声入力ボタンをクリック
    this.voiceButton.click();
    this.isRecording = true;
    
    console.log('✅ 音声入力開始');
  }
  
  async stopVoiceInput() {
    if (!this.voiceButton) {
      console.error('❌ 音声入力ボタンが見つかりません');
      return;
    }
    
    // 音声入力停止（再度クリック）
    this.voiceButton.click();
    this.isRecording = false;
    
    console.log('✅ 音声入力停止');
    
    // 自動送信が有効な場合
    if (this.settings.autoSend) {
      // 500ms待機（テキスト変換完了待ち）
      await this.sleep(500);
      
      // 送信ボタンを探してクリック
      this.sendMessage();
    }
  }
  
  findVoiceButton() {
    // Claude.aiの音声入力ボタンを探す
    // 複数のセレクタパターンを試行
    
    const selectors = [
      'button[aria-label*="voice"]',
      'button[aria-label*="音声"]',
      'button[aria-label*="Voice"]',
      'button[aria-label*="microphone"]',
      'button[aria-label*="マイク"]',
      'button[data-testid*="voice"]',
      'button[class*="voice"]',
      'button svg[class*="microphone"]',
      'button svg[class*="mic"]'
    ];
    
    for (const selector of selectors) {
      const button = document.querySelector(selector);
      if (button) {
        console.log('✅ 音声ボタン検出（セレクタ: ' + selector + '）');
        return button;
      }
    }
    
    // フォールバック: すべてのbuttonを探索
    const allButtons = document.querySelectorAll('button');
    for (const button of allButtons) {
      const ariaLabel = button.getAttribute('aria-label') || '';
      const title = button.getAttribute('title') || '';
      const text = button.textContent || '';
      
      if (
        ariaLabel.toLowerCase().includes('voice') ||
        ariaLabel.toLowerCase().includes('音声') ||
        ariaLabel.toLowerCase().includes('microphone') ||
        ariaLabel.toLowerCase().includes('マイク') ||
        title.toLowerCase().includes('voice') ||
        title.toLowerCase().includes('音声') ||
        text.toLowerCase().includes('voice') ||
        text.toLowerCase().includes('音声')
      ) {
        console.log('✅ 音声ボタン検出（フォールバック検索）');
        return button;
      }
    }
    
    console.warn('⚠️ 音声入力ボタンが見つかりません');
    return null;
  }
  
  sendMessage() {
    // 送信ボタンを探す
    const sendButton = this.findSendButton();
    
    if (!sendButton) {
      console.error('❌ 送信ボタンが見つかりません');
      return;
    }
    
    console.log('🔍 送信ボタン検出:', sendButton);
    
    // 送信ボタンをクリック
    sendButton.click();
    
    console.log('✅ メッセージ送信完了');
  }
  
  findSendButton() {
    // Claude.aiの送信ボタンを探す
    
    const selectors = [
      'button[aria-label*="send"]',
      'button[aria-label*="送信"]',
      'button[aria-label*="Send"]',
      'button[data-testid*="send"]',
      'button[type="submit"]',
      'button svg[class*="send"]',
      'button svg[class*="arrow"]'
    ];
    
    for (const selector of selectors) {
      const button = document.querySelector(selector);
      if (button) {
        // disabled属性がないことを確認
        if (!button.disabled) {
          console.log('✅ 送信ボタン検出（セレクタ: ' + selector + '）');
          return button;
        }
      }
    }
    
    // フォールバック: すべてのbuttonを探索
    const allButtons = document.querySelectorAll('button');
    for (const button of allButtons) {
      if (button.disabled) continue;
      
      const ariaLabel = button.getAttribute('aria-label') || '';
      const title = button.getAttribute('title') || '';
      
      if (
        ariaLabel.toLowerCase().includes('send') ||
        ariaLabel.toLowerCase().includes('送信') ||
        title.toLowerCase().includes('send') ||
        title.toLowerCase().includes('送信')
      ) {
        console.log('✅ 送信ボタン検出（フォールバック検索）');
        return button;
      }
    }
    
    console.warn('⚠️ 送信ボタンが見つかりません');
    return null;
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// 初期化
const voiceHotkey = new ClaudeVoiceHotkey();
