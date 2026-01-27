/**
 * VRM Model Connector - VMC Protocol Implementation
 * VSeeFace, 3tene, VMagicMirror等のVRM対応ソフトウェアと連携
 * OSC (Open Sound Control) over WebSocketを使用
 */

class VRMConnector {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.port = 39540; // VMC Protocol default port
    this.bridgePort = 8765; // WebSocket bridge server port
    this.pluginName = "Zundamon Voice Browser Skill";
    this.reconnectInterval = null;
    this.currentMouthValue = 0;
    
    // VRMのBlendShape名（母音ベース）
    this.vowelBlendShapes = {
      'A': 0,
      'I': 0,
      'U': 0,
      'E': 0,
      'O': 0
    };
  }
  
  async connect() {
    try {
      // WebSocket bridgeサーバーに接続（OSC over WebSocket）
      this.ws = new WebSocket(`ws://localhost:${this.bridgePort}`);
      
      this.ws.onopen = () => {
        console.log('✅ VRM WebSocket Bridge接続成功');
        this.isConnected = true;
        
        // 再接続インターバルをクリア
        if (this.reconnectInterval) {
          clearInterval(this.reconnectInterval);
          this.reconnectInterval = null;
        }
      };
      
      this.ws.onclose = () => {
        console.log('❌ VRM WebSocket Bridge切断');
        this.isConnected = false;
        this.startReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error('❌ VRM WebSocket Bridgeエラー:', error);
        this.isConnected = false;
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 VRM Bridgeメッセージ受信:', data);
        } catch (err) {
          console.warn('⚠️ VRM Bridgeメッセージ解析失敗:', err);
        }
      };
      
    } catch (error) {
      console.error('❌ VRM WebSocket Bridge接続失敗:', error);
      this.startReconnect();
      throw error;
    }
  }
  
  startReconnect() {
    if (this.reconnectInterval) return;
    
    console.log('🔄 VRM WebSocket Bridge再接続を5秒後に試行...');
    this.reconnectInterval = setInterval(() => {
      if (!this.isConnected) {
        console.log('🔄 VRM WebSocket Bridge再接続試行中...');
        this.connect().catch(() => {
          // エラーは無視（再試行継続）
        });
      }
    }, 5000);
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    if (this.reconnectInterval) {
      clearInterval(this.reconnectInterval);
      this.reconnectInterval = null;
    }
    
    this.isConnected = false;
    console.log('🔌 VRM WebSocket Bridge切断完了');
  }
  
  /**
   * 口パクパラメータを設定（0-1の範囲）
   * 音量に応じて母音BlendShapeを制御
   */
  async setMouthOpen(value) {
    if (!this.isConnected) {
      return false;
    }
    
    try {
      // 音量値を0-1の範囲にクランプ
      const clampedValue = Math.max(0, Math.min(1, value));
      this.currentMouthValue = clampedValue;
      
      // 音量が小さい場合は口を閉じる
      if (clampedValue < 0.05) {
        await this.setAllVowels(0);
        return true;
      }
      
      // 音量に応じて母音を段階的に開く
      // 小さい音量: "I" (狭い口)
      // 中程度の音量: "E" (中程度の口)
      // 大きい音量: "A" (大きく開いた口)
      
      if (clampedValue < 0.3) {
        // 小さい音量: I優勢
        await this.setVowel('I', clampedValue * 2); // 0-0.6の範囲
      } else if (clampedValue < 0.6) {
        // 中程度の音量: E優勢
        await this.setVowel('E', (clampedValue - 0.3) * 2 + 0.3); // 0.3-0.9の範囲
      } else {
        // 大きい音量: A優勢
        await this.setVowel('A', (clampedValue - 0.6) * 2 + 0.5); // 0.5-1.0の範囲
      }
      
      return true;
      
    } catch (error) {
      console.error('❌ VRM口パクパラメータ送信エラー:', error);
      return false;
    }
  }
  
  /**
   * 特定の母音BlendShapeを設定
   */
  async setVowel(vowel, value) {
    // 他の母音をゼロにリセット
    for (const v in this.vowelBlendShapes) {
      if (v !== vowel) {
        this.vowelBlendShapes[v] = 0;
      }
    }
    
    // 指定された母音を設定
    this.vowelBlendShapes[vowel] = value;
    
    // VMC Protocolメッセージを送信
    await this.sendBlendShapeValues();
  }
  
  /**
   * すべての母音を同じ値に設定
   */
  async setAllVowels(value) {
    for (const vowel in this.vowelBlendShapes) {
      this.vowelBlendShapes[vowel] = value;
    }
    
    await this.sendBlendShapeValues();
  }
  
  /**
   * VMC ProtocolのBlendShape値を送信
   */
  async sendBlendShapeValues() {
    if (!this.isConnected || !this.ws) {
      return;
    }
    
    try {
      // OSCメッセージをWebSocket経由で送信
      // フォーマット: { type: "blend", shapes: { "A": 0.5, "I": 0.0, ... } }
      const message = {
        type: 'blend',
        shapes: { ...this.vowelBlendShapes }
      };
      
      this.ws.send(JSON.stringify(message));
      
    } catch (error) {
      console.error('❌ VRM BlendShape送信エラー:', error);
    }
  }
  
  /**
   * 腕のポーズを設定（音声再生時の制御）
   * @param {boolean} isPlaying - true: 腕を下げる, false: T-Poseに戻す
   */
  async setArmPose(isPlaying) {
    console.log(`🔍 setArmPose呼び出し: isConnected=${this.isConnected}, ws=${!!this.ws}`);
    if (!this.isConnected || !this.ws) {
      console.warn('⚠️ VRM未接続のため腕ポーズ設定をスキップ');
      return false;
    }
    
    try {
      const message = {
        type: 'setArmPose',
        isPlaying: isPlaying
      };
      
      this.ws.send(JSON.stringify(message));
      console.log(`🎵 腕ポーズ設定: ${isPlaying ? '下げる' : 'T-Pose'}`);
      return true;
      
    } catch (error) {
      console.error('❌ VRM腕ポーズ送信エラー:', error);
      return false;
    }
  }
  
  /**
   * 感情表現を設定（BlendShape制御）
   * @param {string} emotion - 感情名（joy, sad, angry, surprised, 等）
   * @param {number} intensity - 強度 (0.0-1.0)
   */
  async setEmotion(emotion, intensity) {
    if (!this.isConnected || !this.ws) return false;
    
    try {
      const message = {
        type: 'setEmotion',
        emotion: emotion,
        intensity: intensity
      };
      
      this.ws.send(JSON.stringify(message));
      console.log(`🎭 感情設定: ${emotion} (強度: ${intensity})`);
      return true;
      
    } catch (error) {
      console.error('❌ VRM感情送信エラー:', error);
      return false;
    }
  }
  
  /**
   * ジェスチャーを設定（ボーン制御）
   * @param {string} emotion - 感情名（ジェスチャーマッピング用）
   * @param {number} intensity - 強度 (0.0-1.0)
   */
  async setGesture(emotion, intensity) {
    if (!this.isConnected || !this.ws) return false;
    
    try {
      const message = {
        type: 'setGesture',
        emotion: emotion,
        intensity: intensity
      };
      
      this.ws.send(JSON.stringify(message));
      console.log(`👋 ジェスチャー設定: ${emotion} (強度: ${intensity})`);
      return true;
      
    } catch (error) {
      console.error('❌ VRMジェスチャー送信エラー:', error);
      return false;
    }
  }
}

// グローバルインスタンス作成
window.vrmConnector = new VRMConnector();
