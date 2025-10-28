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
    this.userMessageDetected = false;
    this.processedElements = new WeakSet();
    this.isPlaying = false; // 再生中フラグ（同時再生防止）
    this.processingQueue = []; // 処理待ちキュー
    
    this.init();
  }
  
  async init() {
    const settings = await chrome.storage.sync.get(['enabled']);
    this.isEnabled = settings.enabled !== false;
    
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // ページロード後5秒待機してから監視開始（既存メッセージを無視）
    console.log('🔊 Zundamon Voice for Claude: 起動完了（5秒後に監視開始）');
    setTimeout(() => {
      this.userMessageDetected = true;
      this.startObserving();
      console.log('✅ Claude応答の監視を開始しました');
    }, 5000);
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
    
    // Claudeの応答のみを検出（ユーザーメッセージを除外）
    const claudeSelectors = [
      '[data-is-streaming]',
      '[data-test-render-count]',
      '.font-claude-message'
    ];
    
    for (const selector of claudeSelectors) {
      if (element.matches && element.matches(selector)) {
        const isUserMessage = element.closest('[data-testid*="user"]') || 
                             element.querySelector('[data-testid*="user"]');
        
        if (!isUserMessage) {
          console.log('🔍 Claude応答を検出:', element.className);
          
          // ストリーミング中か確認
          const isStreaming = element.getAttribute('data-is-streaming') === 'true';
          
          if (isStreaming) {
            console.log('⏳ ストリーミング中、完了待ち...');
            // ストリーミング完了を待つ
            this.waitForStreamingComplete(element);
          } else {
            console.log('✅ ストリーミング完了、処理開始');
            this.processClaudeMessage(element);
          }
        }
        return;
      }
      
      const messages = element.querySelectorAll(selector);
      messages.forEach(msg => {
        const isUserMessage = msg.closest('[data-testid*="user"]') || 
                             msg.querySelector('[data-testid*="user"]');
        if (!isUserMessage) {
          console.log('🔍 Claude応答を検出:', msg.className);
          
          const isStreaming = msg.getAttribute('data-is-streaming') === 'true';
          
          if (isStreaming) {
            console.log('⏳ ストリーミング中、完了待ち...');
            this.waitForStreamingComplete(msg);
          } else {
            console.log('✅ ストリーミング完了、処理開始');
            this.processClaudeMessage(msg);
          }
        }
      });
    }
  }
  
  waitForStreamingComplete(element) {
    // 属性の変化を監視
    const observer = new MutationObserver((mutations) => {
      const isStreaming = element.getAttribute('data-is-streaming') === 'true';
      
      if (!isStreaming) {
        console.log('✅ ストリーミング完了を検出');
        observer.disconnect();
        // 少し待ってから処理（DOMが完全に更新されるのを待つ）
        setTimeout(() => {
          this.processClaudeMessage(element);
        }, 500);
      }
    });
    
    observer.observe(element, {
      attributes: true,
      attributeFilter: ['data-is-streaming']
    });
    
    // タイムアウト設定（10秒後に強制処理）
    setTimeout(() => {
      observer.disconnect();
      console.log('⚠️ タイムアウト、強制処理');
      this.processClaudeMessage(element);
    }, 10000);
  }
  
  processClaudeMessage(element) {
    // 処理済み要素をスキップ
    if (this.processedElements.has(element)) {
      console.log('⏭️ 処理済み要素をスキップ');
      return;
    }
    this.processedElements.add(element);
    
    const text = this.extractText(element);
    console.log('🔍 抽出されたテキスト:', text ? `"${text.substring(0, 100)}"` : '(空)');
    
    if (!text || text === this.lastProcessedText) {
      console.log('❌ テキストが空または重複:', { isEmpty: !text, isDuplicate: text === this.lastProcessedText });
      return;
    }
    
    const textToSpeak = this.summarizeIfNeeded(text);
    console.log('📝 要約後のテキスト:', textToSpeak.length, '文字');
    
    if (textToSpeak.length > 0) {
      this.lastProcessedText = text;
      console.log('🗣️ 読み上げ開始:', textToSpeak.substring(0, 50));
      this.speakText(textToSpeak);
    } else {
      console.log('❌ 要約後のテキストが空');
    }
  }
  
  extractText(element) {
    const clone = element.cloneNode(true);
    
    // 除外する要素（コードブロック、ツール、思考プロセス、UI要素）
    const excludeSelectors = [
      'pre', 
      'code', 
      'button',  // ボタン要素（「再試行」など）
      '[class*="tool"]', 
      '[class*="thinking"]',
      '[class*="Thinking"]',
      '[data-thinking]',
      '[aria-label*="thinking"]',
      '[aria-label*="Thinking"]',
      '[data-testid*="thinking"]',
      '.thinking-block',
      '.thought-process'
    ];
    
    excludeSelectors.forEach(selector => {
      try {
        clone.querySelectorAll(selector).forEach(el => el.remove());
      } catch (e) {
        // セレクターエラーを無視
      }
    });
    
    let text = clone.textContent.trim();
    console.log('📝 extractText: 初期テキスト:', text.substring(0, 200));
    
    // 思考プロセス部分を正規表現で削除（文字列全体から）
    // 「考え中...」から最初の日本語の挨拶までを削除
    text = text.replace(/考え中[\s\S]*?(?=[ぁ-んァ-ヶー][ぁ-んァ-ヶーー一-龠]{2,})/g, '');
    
    // 思考プロセス全体を一括削除（文の終わりまで続く思考プロセスブロック）
    // 「ユーザーが〜」で始まり、実際の応答（「そうですね」「はい」など）までの全テキストを削除
    text = text.replace(/ユーザー[がはに].+?(?=そうですね|はい|いいえ|ありがとう|わかりました|こんにちは|こんばんは|おはよう|では|それでは)/gs, '');
    
    // 英語・日本語混合の思考プロセス文を個別に削除
    const thinkingPatterns = [
      // 英語の思考プロセス
      /The user is .+?\./g,
      /The user has .+?\./g,
      /The user wrote .+?\./g,
      /I should .+?\./g,
      /Since .+?\./g,
      /This is .+?\./g,
      // 日本語の思考プロセス（「ユーザーは」「ユーザーが」で始まる文）
      /ユーザーは.+?[。\.]/g,
      /ユーザーが.+?[。\.]/g,
      /ユーザーに.+?[。\.]/g,
      // 「これは」「それは」などで始まる説明文（思考プロセスの続き）
      /これは.+?[。\.]/g,
      /それは.+?[。\.]/g,
      /自然な.+?[。\.]/g,
      // 場所情報の言及
      /ユーザーの場所は.+?[。\.]/g,
      // 思考プロセス特有のフレーズ（断片削除）
      /.+?と返答しました[。\.]?/g,
      /.+?のようです[。\.]?/g,
      /.+?が良さそうです[。\.]?/g,
      /.+?待っています[。\.]?/g,
      /何か具体的な.+?[。\.]/g,
      /何か.+?のようなので、.+?[。\.]/g,
      /無理に.+?[。\.]/g,
      // その他の思考プロセスパターン
      /考えていること.+?[。\.]/g,
      /思考プロセス.+?[。\.]/g
    ];
    
    thinkingPatterns.forEach(pattern => {
      text = text.replace(pattern, '');
    });
    
    console.log('🧹 extractText: 思考ブロック削除後:', text.substring(0, 200));
    
    // UI要素のテキストを削除
    const uiTexts = ['再試行', 'Retry', 'コピー', 'Copy'];
    uiTexts.forEach(uiText => {
      text = text.replace(new RegExp(uiText, 'g'), '');
    });
    
    // 複数の改行・空白を整理
    text = text.replace(/\n{2,}/g, '\n').replace(/\s{2,}/g, ' ').trim();
    
    // 空白のみのテキストを除外
    if (text.length === 0) {
      console.log('⚠️ extractText: 空のテキスト');
      return '';
    }
    
    // 日本語が含まれているか確認
    const hasJapanese = /[ぁ-んァ-ヶー一-龠]/.test(text);
    if (!hasJapanese) {
      console.log('⚠️ extractText: 日本語が含まれていないためスキップ');
      return '';
    }
    
    // 短すぎるテキストを除外（3文字未満）
    if (text.length < 3) {
      console.log('⚠️ extractText: テキストが短すぎる:', text.length, '文字');
      return '';
    }
    
    console.log('✅ extractText: 最終テキスト:', text.substring(0, 100));
    return text;
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
    // 既に再生中の場合はキューに追加
    if (this.isPlaying) {
      console.log('⏳ 音声再生中のためキューに追加:', text.substring(0, 30));
      this.processingQueue.push(text);
      return;
    }
    
    this.isPlaying = true;
    
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
    } finally {
      this.isPlaying = false;
      
      // キューに残っているテキストがあれば次を再生
      if (this.processingQueue.length > 0) {
        const nextText = this.processingQueue.shift();
        console.log('📤 キューから次のテキストを再生:', nextText.substring(0, 30));
        setTimeout(() => this.speakText(nextText), 500); // 500ms待機してから次を再生
      }
    }
  }
  
  async synthesizeViaBackground(text) {
    return new Promise((resolve) => {
      console.log('🔧 [Content] メッセージ送信前:', { action: 'synthesize', text, speakerID: this.speakerID });
      
      chrome.runtime.sendMessage({
        action: 'synthesize',
        text: text,
        speakerID: this.speakerID
      }, (response) => {
        console.log('🔧 [Content] メッセージ送信後 レスポンス:', response);
        
        if (chrome.runtime.lastError) {
          console.error('❌ [Content] chrome.runtime.lastError:', chrome.runtime.lastError);
          resolve({ success: false, error: chrome.runtime.lastError.message });
        } else {
          resolve(response || { success: false, error: 'No response' });
        }
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
