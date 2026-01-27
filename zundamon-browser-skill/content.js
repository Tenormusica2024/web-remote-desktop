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
    this.prefetchCache = new Map(); // プリフェッチキャッシュ（複数チャンク対応）
    this.prefetchInProgress = new Set(); // プリフェッチ実行中のテキスト
    this.vtsEnabled = false; // VTubeStudio連携有効フラグ
    this.vrmEnabled = false; // VRM連携有効フラグ
    this.vrmConnected = false; // VRM接続状態（ISOLATED worldで管理）
    
    this.init();
  }
  
  async init() {
    const settings = await chrome.storage.sync.get(['enabled', 'vtsEnabled', 'vrmEnabled']);
    this.isEnabled = settings.enabled !== false;
    this.vtsEnabled = settings.vtsEnabled === true;
    this.vrmEnabled = settings.vrmEnabled === true;
    
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // VTubeStudio接続試行
    if (this.vtsEnabled && window.vtsConnector) {
      console.log('🎭 VTubeStudio接続を試行中...');
      window.vtsConnector.connect()
        .then(() => {
          console.log('✅ VTubeStudio連携が有効になりました');
        })
        .catch(err => {
          console.warn('⚠️ VTubeStudio接続失敗（口パクなしで動作）:', err);
        });
    }
    
    // VRM接続試行（postMessage経由）
    if (this.vrmEnabled) {
      this.vrmConnect();
      // 接続後、常に腕を下げた状態に設定
      setTimeout(() => {
        this.vrmSetArmPose(true);
        console.log('🎵 VRM初期化: 腕を下げた状態に設定');
      }, 2000); // 接続完了を待つ
    }
    
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
        // 即座に処理開始（遅延削除）
        this.processClaudeMessage(element);
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
    if (this.processedElements.has(element)) return;
    this.processedElements.add(element);
    
    const text = this.extractText(element);
    console.log('🔍 抽出テキスト:', text ? text.substring(0, 100) : '(空)');
    if (!text || text === this.lastProcessedText) {
      console.log('⚠️ テキスト処理スキップ:', !text ? 'テキストなし' : '既に処理済み');
      return;
    }
    
    const textToSpeak = this.summarizeIfNeeded(text);
    console.log('📝 要約後テキスト:', textToSpeak ? textToSpeak.substring(0, 100) : '(空)');
    if (textToSpeak.length === 0) {
      console.log('⚠️ 要約後テキストが空のためスキップ');
      return;
    }
    
    this.lastProcessedText = text;
    
    // 長文の場合は分割して段階的に読み上げ
    const chunks = this.splitTextForReading(textToSpeak);
    console.log('📦 チャンク数:', chunks.length, '最初のチャンク:', chunks[0] ? chunks[0].substring(0, 50) : '(なし)');
    
    // 各チャンクに対して感情を分析して保存
    const emotionTimeline = chunks.map(chunk => {
      const emotion = this.analyzeEmotionFromText(chunk);
      console.log('🎭 チャンク感情分析:', chunk.substring(0, 30), '→', emotion);
      return { chunk, emotion };
    });
    
    // すべてのチャンクを並列でプリフェッチ開始（最初のチャンクも含む）
    const prefetchCount = Math.min(5, chunks.length); // 最大5チャンクまで並列プリフェッチ
    for (let i = 0; i < prefetchCount; i++) {
      this.startPrefetch(chunks[i]);
    }
    
    // プリフェッチ開始後、順次再生開始（感情タイムラインを渡す）
    emotionTimeline.forEach(item => this.speakText(item.chunk, item.emotion));
  }
  
  splitTextForReading(text) {
    // 50文字以下なら分割不要
    if (text.length <= 50) {
      return [text];
    }
    
    const chunks = [];
    const maxChunkSize = 50;
    
    // 句点・改行・読点で分割候補を作成
    const segments = text.split(/([。！？\n、])/);
    
    let currentChunk = '';
    
    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      
      // 区切り文字自体は前のセグメントに結合
      if (segment.match(/[。！？\n、]/)) {
        currentChunk += segment;
        
        // 50文字超えたら、または句点・改行の場合はチャンク確定
        if (currentChunk.length >= maxChunkSize || segment.match(/[。！？\n]/)) {
          if (currentChunk.trim().length > 0) {
            chunks.push(currentChunk.trim());
            currentChunk = '';
          }
        }
      } else {
        // 追加すると50文字超える場合
        if (currentChunk.length > 0 && (currentChunk + segment).length > maxChunkSize) {
          // 現在のチャンクを確定
          if (currentChunk.trim().length > 0) {
            chunks.push(currentChunk.trim());
          }
          currentChunk = segment;
        } else {
          currentChunk += segment;
        }
      }
    }
    
    // 残りのチャンクを追加
    if (currentChunk.trim().length > 0) {
      chunks.push(currentChunk.trim());
    }
    
    return chunks;
  }
  
  /**
   * テキストから感情を分析（ルールベース）
   * @param {string} text - 分析対象テキスト
   * @return {Object} { emotion: string, intensity: number }
   */
  analyzeEmotionFromText(text) {
    // 感情パターン定義（正規表現 + 強度）
    const emotionPatterns = [
      // 喜び・嬉しい系
      { emotion: 'joy', pattern: /(嬉しい|楽しい|幸せ|良かった|やった|わーい|わあい|最高|素晴らしい|素敵|ありがとう|感謝|やりました|成功|達成|完璧|良好|順調|うまくいき|喜んで|おめでとう|祝|ハッピー|ラッキー)/i, intensity: 0.8 },
      { emotion: 'joy', pattern: /(笑|ハハ|ふふ|にこ|ニコ|😊|😄|🎉|✨)/i, intensity: 0.6 },
      
      // 悲しみ・残念系
      { emotion: 'sad', pattern: /(悲しい|辛い|寂しい|残念|がっかり|泣|涙|失敗|だめ|ダメ|諦め|無理|厳しい|困難|苦しい|悔しい|心配|不安|😢|😭)/i, intensity: 0.8 },
      { emotion: 'sad', pattern: /(うーん|むむ|んー|あー)/i, intensity: 0.4 },
      
      // 呆れた・やれやれ系
      { emotion: 'exasperated', pattern: /(呆れ|やれやれ|はぁ|呆|あきれ|もう\.\.\.|またか|いい加減)/i, intensity: 0.8 },
      
      // 驚き系
      { emotion: 'surprised', pattern: /(驚|びっくり|えっ|え！|まさか|信じられない|すごい|すげえ|なんと|おお|わお|うわ|へえ|ほう|おや|あら|まあ|😲|😮|‼️)/i, intensity: 0.8 },
      { emotion: 'surprised', pattern: /(！|!){2,}/i, intensity: 0.7 },
      
      // 怒り・不満系
      { emotion: 'angry', pattern: /(怒|腹立|ムカ|イライラ|許せない|ふざけ|おかしい|変だ|最悪|ひどい|いい加減|勘弁|やめて|うるさい|うざ|💢|😠|😡)/i, intensity: 0.8 },
      
      // 困惑・混乱系
      { emotion: 'confused', pattern: /(困|わからない|不明|謎|どうして|なぜ|理解できない|意味不明|混乱|ややこしい|複雑|難しい|迷|どうすれば|😕|🤔)/i, intensity: 0.7 },
      
      // 心配・不安系（大丈夫？系を含む）
      { emotion: 'worried', pattern: /(大丈夫\?|大丈夫かな|大丈夫なのだ\?|心配|不安|危険|リスク|問題|トラブル|エラー|警告|注意|確認|気をつけ|慎重|懸念|危惧)/i, intensity: 0.7 },
      
      // 興奮・ワクワク系
      { emotion: 'excited', pattern: /(興奮|ワクワク|楽しみ|期待|待ち遠しい|待ちきれない|いよいよ|ついに|やっと|さあ|よし|頑張|🔥|💪|🚀)/i, intensity: 0.8 },
      
      // 謝罪・申し訳ない系
      { emotion: 'apologetic', pattern: /(すみません|ごめん|申し訳|失礼|お詫び|反省|謝|許して|ミス|間違|誤)/i, intensity: 0.7 },
      
      // 感謝系（喜びとは別の表情）
      { emotion: 'grateful', pattern: /(ありがとう|感謝|お礼|恩|助かり|サンクス|thanks|thank|恐縮|恐れ入り)/i, intensity: 0.8 },
      
      // 励まし・応援系（大丈夫！系を含む）
      { emotion: 'encouraging', pattern: /(大丈夫！|大丈夫だよ|大丈夫です|大丈夫なのだ(?![？\?])|心配ない|問題ない|頑張|応援|ファイト|やれる|できる|いける|いけます|👍|💪)/i, intensity: 0.8 },
      
      // 説明・解説系（落ち着いた表情）
      { emotion: 'explaining', pattern: /(説明|解説|つまり|要するに|具体的|詳しく|まず|次に|最後に|ステップ|手順|方法|理由|原因|これは|それは|という|ため|ので)/i, intensity: 0.5 },
      
      // 質問系（正規表現エラー修正：全角？を除去）
      { emotion: 'questioning', pattern: /(\?|ですか|ますか|でしょうか|かな|かしら|どう|何|誰|いつ|どこ|なぜ|どのように)/i, intensity: 0.6 },
      
      // 祝福・お祝い系
      { emotion: 'celebrating', pattern: /(おめでとう|祝|お祝い|成功|達成|完了|やりました|勝利|優勝|合格|🎉|🎊|🎈)/i, intensity: 0.9 },
      
      // 失望・がっかり系
      { emotion: 'disappointed', pattern: /(失望|がっかり|期待外れ|残念|だめ|無理|諦め|見込みなし|希望なし)/i, intensity: 0.7 },
      
      // 感心・感動系
      { emotion: 'impressed', pattern: /(感心|感動|素晴らしい|見事|さすが|流石|立派|すごい|すばらしい|感銘|圧倒|👏|✨)/i, intensity: 0.8 },
      
      // ふざけ・遊び系
      { emotion: 'playful', pattern: /(ふふ|えへ|てへ|にや|むふ|わーい|やったー|イェイ|イエイ|😜|😝|🤪)/i, intensity: 0.7 },
      
      // 真剣・深刻系
      { emotion: 'serious', pattern: /(重要|深刻|緊急|至急|必須|絶対|確実|真剣|本気|厳密|厳格|正確|必ず|⚠️|🚨)/i, intensity: 0.8 }
    ];
    
    // テキスト全体をチェックして最も強い感情を検出
    let detectedEmotion = { emotion: 'neutral', intensity: 0 };
    
    for (const pattern of emotionPatterns) {
      if (pattern.pattern.test(text)) {
        // 複数マッチした場合は最も強度の高いものを採用
        if (pattern.intensity > detectedEmotion.intensity) {
          detectedEmotion = { emotion: pattern.emotion, intensity: pattern.intensity };
        }
      }
    }
    
    return detectedEmotion;
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
    
    // 思考プロセス部分を正規表現で削除（文字列全体から）
    text = text.replace(/考え中[\s\S]*?(?=[ぁ-んァ-ヶー][ぁ-んァ-ヶーー一-龠]{2,})/g, '');
    text = text.replace(/ユーザー[がはに].+?(?=そうですね|はい|いいえ|ありがとう|わかりました|こんにちは|こんばんは|おはよう|では|それでは)/gs, '');
    
    // 英語・日本語混合の思考プロセス文を個別に削除
    const thinkingPatterns = [
      /The user is .+?\./g,
      /The user has .+?\./g,
      /The user wrote .+?\./g,
      /I should .+?\./g,
      /Since .+?\./g,
      /This is .+?\./g,
      /ユーザーは.+?[。\.]/g,
      /ユーザーが.+?[。\.]/g,
      /ユーザーに.+?[。\.]/g,
      /これは.+?[。\.]/g,
      /それは.+?[。\.]/g,
      /自然な.+?[。\.]/g,
      /ユーザーの場所は.+?[。\.]/g,
      /.+?と返答しました[。\.]?/g,
      /.+?のようです[。\.]?/g,
      /.+?が良さそうです[。\.]?/g,
      /.+?待っています[。\.]?/g,
      /何か具体的な.+?[。\.]/g,
      /何か.+?のようなので、.+?[。\.]/g,
      /無理に.+?[。\.]/g,
      /考えていること.+?[。\.]/g,
      /思考プロセス.+?[。\.]/g
    ];
    
    thinkingPatterns.forEach(pattern => {
      text = text.replace(pattern, '');
    });
    
    // UI要素のテキストを削除
    const uiTexts = ['再試行', 'Retry', 'コピー', 'Copy'];
    uiTexts.forEach(uiText => {
      text = text.replace(new RegExp(uiText, 'g'), '');
    });
    
    // 複数の改行・空白を整理
    text = text.replace(/\n{2,}/g, '\n').replace(/\s{2,}/g, ' ').trim();
    
    // 空白のみのテキストを除外
    if (text.length === 0) return '';
    
    // 日本語が含まれているか確認
    const hasJapanese = /[ぁ-んァ-ヶー一-龠]/.test(text);
    if (!hasJapanese) return '';
    
    // 短すぎるテキストを除外（3文字未満）
    if (text.length < 3) return '';
    
    return text;
  }
  
  summarizeIfNeeded(text) {
    // 全文を読み上げる（要約なし）
    return text;
  }
  
  async speakText(text, emotion = null) {
    // 既に再生中の場合はキューに追加（感情情報も一緒に）
    if (this.isPlaying) {
      this.processingQueue.push({ text, emotion });
      // キューに追加した瞬間に次のチャンクのプリフェッチを開始
      if (this.processingQueue.length === 1 && !this.prefetchInProgress.has(text)) {
        this.startPrefetch(text);
      }
      return;
    }
    
    this.isPlaying = true;
    
    // VRM感情表現設定（チャンク再生前）
    if (this.vrmEnabled && this.vrmConnected && emotion) {
      if (emotion.emotion !== 'neutral') {
        // 感情がある場合は表情とジェスチャーを設定
        await this.vrmSetEmotion(emotion.emotion, emotion.intensity);
        await this.vrmSetGesture(emotion.emotion, emotion.intensity);
        console.log('🎭 表情変更:', emotion.emotion, '強度:', emotion.intensity);
      } else {
        // neutralの場合は表情をリセット
        await this.vrmSetEmotion('neutral', 0);
        console.log('😐 表情リセット（neutral）');
      }
    }
    
    try {
      // プリフェッチ完了を待機（最大3秒）
      const maxWait = 3000;
      const startTime = Date.now();
      while (!this.prefetchCache.has(text) && 
             this.prefetchInProgress.has(text) && 
             Date.now() - startTime < maxWait) {
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      
      // プリフェッチ成功時はキャッシュを使用
      if (this.prefetchCache.has(text)) {
        const audioData = this.prefetchCache.get(text);
        this.prefetchCache.delete(text);
        
        // 次のチャンクをプリフェッチ
        if (this.processingQueue.length > 0 && !this.prefetchInProgress.has(this.processingQueue[0].text)) {
          const nextItem = this.processingQueue[0];
          this.startPrefetch(nextItem.text);
        }
        
        await this.playAudio(audioData);
      } else {
        // プリフェッチ失敗時は通常の合成
        const result = await this.synthesizeViaBackground(text);
        
        if (!result.success) {
          // Extension context無効化などの致命的エラーは静かに終了
          if (result.fatal) {
            return;
          }
          throw new Error(result.error);
        }
        
        // ArrayBufferに変換
        const audioData = new Uint8Array(result.audioData).buffer;
        
        // 再生開始と同時に次のチャンクをプリフェッチ
        if (this.processingQueue.length > 0 && !this.prefetchInProgress.has(this.processingQueue[0].text)) {
          const nextItem = this.processingQueue[0];
          this.startPrefetch(nextItem.text);
        }
        
        // 再生
        await this.playAudio(audioData);
      }
      
    } catch (error) {
      console.error('❌ 音声合成エラー:', error);
    } finally {
      this.isPlaying = false;
      
      // キューに残っているテキストがあれば次を再生（ループ構造）
      while (this.processingQueue.length > 0) {
        const nextItem = this.processingQueue.shift();
        const nextText = nextItem.text;
        const nextEmotion = nextItem.emotion;
        
        // VRM感情表現更新（次のチャンク再生前）
        if (this.vrmEnabled && this.vrmConnected && nextEmotion) {
          if (nextEmotion.emotion !== 'neutral') {
            await this.vrmSetEmotion(nextEmotion.emotion, nextEmotion.intensity);
            await this.vrmSetGesture(nextEmotion.emotion, nextEmotion.intensity);
            console.log('🎭 表情変更:', nextEmotion.emotion, '強度:', nextEmotion.intensity);
          } else {
            await this.vrmSetEmotion('neutral', 0);
            console.log('😐 表情リセット（neutral）');
          }
        }
        
        // プリフェッチ済みの場合は即座に再生
        if (this.prefetchCache.has(nextText)) {
          this.isPlaying = true;
          const cachedAudio = this.prefetchCache.get(nextText);
          this.prefetchCache.delete(nextText);
          
          // 次のチャンクをプリフェッチ
          if (this.processingQueue.length > 0 && !this.prefetchInProgress.has(this.processingQueue[0].text)) {
            const followingItem = this.processingQueue[0];
            this.startPrefetch(followingItem.text);
          }
          
          try {
            await this.playAudio(cachedAudio);
            this.isPlaying = false;
          } catch (err) {
            console.error('❌ 音声再生エラー:', err);
            this.isPlaying = false;
            break;
          }
        } else {
          // キャッシュミス - 再帰呼び出しで処理
          this.prefetchCache.delete(nextText);
          this.speakText(nextText, nextEmotion);
          break;
        }
      }
    }
  }
  
  startPrefetch(text) {
    if (this.prefetchInProgress.has(text) || this.prefetchCache.has(text)) {
      return; // すでにプリフェッチ中またはキャッシュ済み
    }
    
    this.prefetchInProgress.add(text);
    this.synthesizeViaBackground(text).then(result => {
      if (result.success) {
        this.prefetchCache.set(text, new Uint8Array(result.audioData).buffer);
      }
      this.prefetchInProgress.delete(text);
    }).catch(() => {
      this.prefetchInProgress.delete(text);
    });
  }
  
  async synthesizeViaBackground(text, retryCount = 0) {
    const MAX_RETRIES = 2;
    const TIMEOUT_MS = 10000; // 10秒でタイムアウト（短縮して早期リトライ）
    
    // Extension context無効化チェック
    if (!chrome.runtime?.id) {
      console.warn('⚠️ 拡張機能のコンテキストが無効化されています。音声読み上げを停止します。');
      this.isEnabled = false;
      return { success: false, error: 'Extension context invalidated', fatal: true };
    }
    
    return new Promise((resolve) => {
      let timeoutId;
      let messageCompleted = false;
      
      // タイムアウトハンドリング
      timeoutId = setTimeout(() => {
        if (!messageCompleted) {
          messageCompleted = true;
          
          // リトライ可能な場合は再試行（警告レベル）
          if (retryCount < MAX_RETRIES) {
            console.warn(`⚠️ Background Service Worker応答なし、再試行 (${retryCount + 1}/${MAX_RETRIES})`);
            this.synthesizeViaBackground(text, retryCount + 1)
              .then(resolve)
              .catch(() => resolve({ success: false, error: 'Timeout after retry' }));
          } else {
            // リトライ後も失敗した場合のみエラー表示
            console.error('❌ Background Service Worker応答なし（VOICEVOX Engine起動確認してください）');
            resolve({ success: false, error: 'Background Service Worker timeout' });
          }
        }
      }, TIMEOUT_MS);
      
      try {
        // Service Workerをウェイクアップするため、まずpingメッセージを送信
        chrome.runtime.sendMessage({ action: 'ping' }, () => {
          // pingレスポンスを無視して本命のメッセージを送信
          chrome.runtime.sendMessage({
            action: 'synthesize',
            text: text,
            speakerID: this.speakerID
          }, (response) => {
          if (!messageCompleted) {
            messageCompleted = true;
            clearTimeout(timeoutId);
            
            if (chrome.runtime.lastError) {
              const errorMsg = chrome.runtime.lastError.message;
              
              // Extension context invalidated エラーの場合は致命的エラーとして処理
              if (errorMsg.includes('Extension context invalidated')) {
                console.warn('⚠️ 拡張機能が再読み込みされました。音声読み上げを停止します。');
                this.isEnabled = false;
                resolve({ success: false, error: errorMsg, fatal: true });
                return;
              }
              
              // "message port closed" エラーの場合はリトライ（警告レベル）
              if (errorMsg.includes('message port closed') && retryCount < MAX_RETRIES) {
                console.warn(`⚠️ Chrome拡張エラー（${errorMsg}）、再試行します (${retryCount + 1}/${MAX_RETRIES})`);
                this.synthesizeViaBackground(text, retryCount + 1)
                  .then(resolve)
                  .catch(() => resolve({ success: false, error: errorMsg }));
              } else {
                // リトライ後も失敗した場合のみエラー表示
                console.error('❌ Chrome拡張エラー（リトライ後も失敗）:', errorMsg);
                resolve({ success: false, error: errorMsg });
              }
            } else {
              resolve(response || { success: false, error: 'No response' });
            }
          }
          });
        });
      } catch (error) {
        messageCompleted = true;
        clearTimeout(timeoutId);
        console.warn('⚠️ メッセージ送信時にエラーが発生しました:', error.message);
        this.isEnabled = false;
        resolve({ success: false, error: error.message, fatal: true });
      }
    });
  }
  
  async playAudio(arrayBuffer) {
    const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    
    // VTubeStudio/VRM口パク連携用のAnalyserNode追加
    let analyser = null;
    const needsAnalyser = (this.vtsEnabled && window.vtsConnector && window.vtsConnector.isAuthenticated) ||
                          (this.vrmEnabled && this.vrmConnected);
    
    if (needsAnalyser) {
      analyser = this.audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyser.connect(this.audioContext.destination);
    } else {
      source.connect(this.audioContext.destination);
    }
    
    // 音声再生中も腕は下げたまま維持（何もしない）
    
    return new Promise((resolve) => {
      source.onended = () => {
        // 再生終了時に口を閉じる
        if (this.vtsEnabled && window.vtsConnector && window.vtsConnector.isAuthenticated) {
          window.vtsConnector.setMouthOpen(0);
        }
        if (this.vrmEnabled && this.vrmConnected) {
          this.vrmSetMouthOpen(0);
          // 腕は下げたまま維持（T-Poseに戻さない）
        }
        resolve();
      };
      
      source.start(0);
      
      // VTubeStudio口パクアニメーション開始
      if (analyser) {
        this.animateMouth(analyser, source);
      }
    });
  }
  
  animateMouth(analyser, source) {
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    let animationFrameId = null;
    let isOpen = false; // 口の開閉状態
    let frameCount = 0; // フレームカウンタ
    const toggleInterval = 8; // 8フレーム（約133ms）ごとに開閉切り替え
    
    const updateMouth = () => {
      // 音声再生が終了していたらアニメーション停止
      if (source.playbackRate === 0 || (!this.vtsEnabled && !this.vrmEnabled)) {
        if (animationFrameId) {
          cancelAnimationFrame(animationFrameId);
        }
        return;
      }
      
      // 音量データ取得
      analyser.getByteFrequencyData(dataArray);
      
      // 低〜中周波数帯域（人の声）を重視して音量計算
      const voiceRange = dataArray.slice(2, 20);
      const sum = voiceRange.reduce((a, b) => a + b, 0);
      const average = sum / voiceRange.length;
      
      // 音声があるか判定（閾値8以上）
      let mouthValue = 0;
      if (average > 8) {
        // アニメ風の二値的な口パク：開く/閉じるを繰り返す
        frameCount++;
        
        if (frameCount >= toggleInterval) {
          isOpen = !isOpen; // 開閉を反転
          frameCount = 0;
        }
        
        // 開いている時は0.8、閉じている時は0.2
        mouthValue = isOpen ? 0.8 : 0.2;
      } else {
        // 無音時は口を閉じる
        mouthValue = 0;
        isOpen = false;
        frameCount = 0;
      }
      
      // VTubeStudioに口パクパラメータ送信
      if (this.vtsEnabled && window.vtsConnector && window.vtsConnector.isAuthenticated) {
        window.vtsConnector.setMouthOpen(mouthValue);
      }
      
      // VRMに口パクパラメータ送信（postMessage経由）
      if (this.vrmEnabled && this.vrmConnected) {
        this.vrmSetMouthOpen(mouthValue);
      }
      
      // 次のフレーム
      animationFrameId = requestAnimationFrame(updateMouth);
    };
    
    updateMouth();
  }
  
  showNotification(title, message) {
    console.warn(`[${title}] ${message}`);
  }
  
  async setEnabled(enabled) {
    this.isEnabled = enabled;
    await chrome.storage.sync.set({ enabled });
    console.log(`🔊 音声通知: ${enabled ? '有効' : '無効'}`);
  }
  
  // VRM Bridge経由でconnect実行
  vrmConnect() {
    window.postMessage({
      type: 'VRM_BRIDGE',
      method: 'connect'
    }, '*');
    
    // レスポンス待ち受け（1回のみ）
    const responseHandler = (event) => {
      // ISOLATED worldではevent.sourceチェックをスキップ
      if (!event.data || typeof event.data !== 'object') return;
      const { type, method, success } = event.data;
      
      if (type === 'VRM_BRIDGE_RESPONSE' && method === 'connect') {
        if (success) {
          this.vrmConnected = true;
          console.log('✅ VRM接続成功: this.vrmConnected =', this.vrmConnected);
        } else {
          this.vrmConnected = false;
          console.warn('❌ VRM接続失敗: this.vrmConnected =', this.vrmConnected);
        }
        window.removeEventListener('message', responseHandler);
      }
    };
    
    window.addEventListener('message', responseHandler);
  }
  
  // VRM Bridge経由でsetMouthOpen実行（高頻度呼び出し用、レスポンス不要）
  vrmSetMouthOpen(value) {
    if (!this.vrmConnected) {
      return;
    }
    
    // F12ログ抑制（大量ログ防止）
    window.postMessage({
      type: 'VRM_BRIDGE',
      method: 'setMouthOpen',
      params: { value }
    }, '*');
  }
  
  // VRM Bridge経由でsetArmPose実行（音声再生制御用）
  vrmSetArmPose(isPlaying) {
    if (!this.vrmConnected) return;
    
    window.postMessage({
      type: 'VRM_BRIDGE',
      method: 'setArmPose',
      params: { isPlaying }
    }, '*');
  }
  
  // VRM Bridge経由でsetEmotion実行（感情表現制御）
  vrmSetEmotion(emotion, intensity) {
    if (!this.vrmConnected) return;
    
    window.postMessage({
      type: 'VRM_BRIDGE',
      method: 'setEmotion',
      params: { emotion, intensity }
    }, '*');
  }
  
  // VRM Bridge経由でsetGesture実行（ジェスチャー制御）
  vrmSetGesture(emotion, intensity) {
    if (!this.vrmConnected) return;
    
    window.postMessage({
      type: 'VRM_BRIDGE',
      method: 'setGesture',
      params: { emotion, intensity }
    }, '*');
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
